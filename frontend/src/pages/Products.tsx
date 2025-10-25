import React, { useEffect, useState } from 'react';
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import { productAPI } from '../services/api';
import { setProducts, addProduct, updateProduct, deleteProduct, setLoading, setError } from '../store/productsSlice';
import ProductList from '../components/ProductList';
import ProductForm from '../components/ProductForm';
import PermissionGate from '../components/PermissionGate';
import realTimeSyncService from '../services/realTimeSyncService';
import {
  CircularProgress,
  Alert,
  Fab,
  Button,
  Box,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  MenuItem,
  Select,
  FormControl,
  InputLabel
} from '@mui/material';
import { Add as AddIcon, Upload as UploadIcon, Download as DownloadIcon } from '@mui/icons-material';

const Products = () => {
    const dispatch = useAppDispatch();
    const { products, loading, error } = useAppSelector((state) => state.products);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingProduct, setEditingProduct] = useState<any>(null);
    const [isBulkModalOpen, setIsBulkModalOpen] = useState(false);
    const [bulkAction, setBulkAction] = useState<'import' | 'export'>('export');
    const [bulkFormat, setBulkFormat] = useState<'csv' | 'json'>('csv');
    const [bulkFile, setBulkFile] = useState<File | null>(null);
    const [isBulkLoading, setIsBulkLoading] = useState(false);
    const { isAuthenticated } = useAppSelector((state) => state.auth);

    useEffect(() => {
        const fetchProducts = async () => {
            dispatch(setLoading(true));
            dispatch(setError(null));
            
            try {
                const response = await productAPI.getProducts();
                dispatch(setProducts(response.data));
            } catch (err: any) {
                dispatch(setError(err.message || 'Failed to load products'));
            } finally {
                dispatch(setLoading(false));
            }
        };

        if (isAuthenticated) {
            fetchProducts();
        }
    }, [isAuthenticated, dispatch]);

    // Initialize and connect to real-time sync
    useEffect(() => {
        if (isAuthenticated) {
            realTimeSyncService.connect();
        }

        return () => {
            realTimeSyncService.disconnect();
        };
    }, [isAuthenticated]);

    const handleCreateProduct = () => {
        setEditingProduct(null);
        setIsFormOpen(true);
    };

    const handleEditProduct = (product: any) => {
        setEditingProduct(product);
        setIsFormOpen(true);
    };

    const handleFormSubmit = (product: any) => {
        if (editingProduct) {
            // Update existing product
            dispatch(updateProduct(product));
            realTimeSyncService.sendProductUpdate('update', product);
        } else {
            // Add new product
            dispatch(addProduct(product));
            realTimeSyncService.sendProductUpdate('create', product);
        }
        
        setIsFormOpen(false);
    };

    const handleDeleteProduct = (productId: number) => {
        dispatch(deleteProduct(productId));
        realTimeSyncService.sendProductUpdate('delete', { id: productId });
    };

    const handleBulkFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setBulkFile(e.target.files[0]);
        }
    };

    const handleBulkAction = async () => {
        if (bulkAction === 'export') {
            try {
                setIsBulkLoading(true);
                const url = `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/v1/products/bulk/`;
                
                // Create a temporary link to download the file
                const link = document.createElement('a');
                link.href = `${url}?action=export&format=${bulkFormat}`;
                link.download = `products.${bulkFormat}`;
                link.click();
            } catch (error) {
                console.error('Export failed:', error);
            } finally {
                setIsBulkLoading(false);
                setIsBulkModalOpen(false);
            }
        } else if (bulkAction === 'import' && bulkFile) {
            try {
                setIsBulkLoading(true);
                
                const formData = new FormData();
                formData.append('action', 'import');
                formData.append('format', bulkFormat);
                formData.append('file', bulkFile);

                const response = await productAPI.bulkOperation(formData);
                
                // Refresh product list after import
                const refreshResponse = await productAPI.getProducts();
                dispatch(setProducts(refreshResponse.data));
                
                alert(`Successfully imported products from ${bulkFormat.toUpperCase()}`);
            } catch (error) {
                console.error('Import failed:', error);
                alert('Import failed. Please check the file format and try again.');
            } finally {
                setIsBulkLoading(false);
                setIsBulkModalOpen(false);
            }
        }
    };

    const openBulkModal = (action: 'import' | 'export') => {
        setBulkAction(action);
        setIsBulkModalOpen(true);
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <CircularProgress />
            </div>
        );
    }

    if (error) {
        return (
            <div className="container mx-auto px-4 py-8">
                <Alert severity="error">{error}</Alert>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold text-gray-800">Products</h1>
                
                <PermissionGate permission="add_product">
                    <Box display="flex" gap={2}>
                        <Button
                            variant="outlined"
                            startIcon={<DownloadIcon />}
                            onClick={() => openBulkModal('export')}
                        >
                            Export Products
                        </Button>
                        <Button
                            variant="outlined"
                            startIcon={<UploadIcon />}
                            onClick={() => openBulkModal('import')}
                        >
                            Import Products
                        </Button>
                    </Box>
                </PermissionGate>
            </div>
            
            <PermissionGate permission="view_product">
                <div className="bg-white rounded-lg shadow-md p-6">
                    <ProductList 
                        products={products} 
                        onEdit={handleEditProduct} 
                        onDelete={handleDeleteProduct}
                    />
                </div>
            </PermissionGate>
            
            {/* Add Product Floating Action Button - Only show if user can add products */}
            <PermissionGate permission="add_product">
                <Fab 
                    color="primary" 
                    aria-label="add" 
                    style={{ position: 'fixed', bottom: 70, right: 16 }}
                    onClick={handleCreateProduct}
                >
                    <AddIcon />
                </Fab>
            </PermissionGate>
            
            {/* Product Form Modal - Only accessible if user has permissions */}
            <PermissionGate permission="add_product">
                <ProductForm 
                    open={isFormOpen}
                    onClose={() => setIsFormOpen(false)}
                    onSubmit={handleFormSubmit}
                    initialData={editingProduct}
                />
            </PermissionGate>
            
            {/* Bulk Operations Modal */}
            <Dialog open={isBulkModalOpen} onClose={() => setIsBulkModalOpen(false)} maxWidth="sm" fullWidth>
                <DialogTitle>
                    {bulkAction === 'import' ? 'Import Products' : 'Export Products'}
                </DialogTitle>
                <DialogContent>
                    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
                        <FormControl fullWidth>
                            <InputLabel>Format</InputLabel>
                            <Select
                                value={bulkFormat}
                                label="Format"
                                onChange={(e) => setBulkFormat(e.target.value as 'csv' | 'json')}
                            >
                                <MenuItem value="csv">CSV</MenuItem>
                                <MenuItem value="json">JSON</MenuItem>
                            </Select>
                        </FormControl>
                        
                        {bulkAction === 'import' && (
                            <div>
                                <input
                                    accept={bulkFormat === 'csv' ? '.csv' : '.json'}
                                    style={{ display: 'none' }}
                                    id="bulk-upload"
                                    type="file"
                                    onChange={handleBulkFileChange}
                                />
                                <label htmlFor="bulk-upload">
                                    <Button variant="outlined" component="span" fullWidth>
                                        Upload {bulkFormat.toUpperCase()} File
                                    </Button>
                                </label>
                                {bulkFile && (
                                    <div style={{ marginTop: '10px' }}>
                                        Selected: {bulkFile.name}
                                    </div>
                                )}
                            </div>
                        )}
                    </Box>
                </DialogContent>
                <DialogActions>
                    <Button onClick={() => setIsBulkModalOpen(false)}>Cancel</Button>
                    <Button 
                        onClick={handleBulkAction} 
                        variant="contained" 
                        disabled={isBulkLoading || (bulkAction === 'import' && !bulkFile)}
                    >
                        {isBulkLoading ? <CircularProgress size={24} /> : 
                         bulkAction === 'import' ? 'Import' : 'Export'}
                    </Button>
                </DialogActions>
            </Dialog>
        </div>
    );
};

export default Products;