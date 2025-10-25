import React, { useEffect, useState } from 'react';
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import { inventoryAPI, productAPI, warehouseAPI } from '../services/api';
import { setInventory, addInventory, updateInventory, deleteInventory, setLoading, setError } from '../store/inventorySlice';
import { setProducts } from '../store/productsSlice';
import { setWarehouses } from '../store/warehousesSlice';
import InventoryForm from '../components/InventoryForm';
import PermissionGate from '../components/PermissionGate';
import realTimeSyncService from '../services/realTimeSyncService';
import {
  CircularProgress,
  Alert,
  Fab,
  Card,
  CardContent,
  Typography,
  Grid,
  IconButton,
  Box,
  TextField,
  InputLabel,
  MenuItem,
  FormControl,
  Select,
  Chip,
  CardHeader,
  Stack,
  Snackbar,
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, Warning as WarningIcon } from '@mui/icons-material';
import { Inventory } from '../types';

const InventoryPage = () => {
    const dispatch = useAppDispatch();
    const { inventory, loading, error } = useAppSelector((state) => state.inventory);
    const { products } = useAppSelector((state) => state.products);
    const { warehouses } = useAppSelector((state) => state.warehouses);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingInventory, setEditingInventory] = useState<Inventory | null>(null);
    const [filters, setFilters] = useState({
      productId: '',
      warehouseId: '',
      binLocation: ''
    });
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
    const { isAuthenticated } = useAppSelector((state) => state.auth);

    useEffect(() => {
        const fetchInventory = async () => {
            dispatch(setLoading(true));
            dispatch(setError(null));
            
            try {
                const response = await inventoryAPI.getInventory();
                dispatch(setInventory(response.data));
            } catch (err: any) {
                dispatch(setError(err.message || 'Failed to load inventory'));
                showSnackbar(err.message || 'Failed to load inventory', 'error');
            } finally {
                dispatch(setLoading(false));
            }
        };

        if (isAuthenticated) {
            fetchInventory();
        }
    }, [isAuthenticated, dispatch]);

    // Load products and warehouses
    useEffect(() => {
        const fetchProducts = async () => {
            if (isAuthenticated) {
                try {
                    const response = await productAPI.getProducts();
                    dispatch(setProducts(response.data));
                } catch (err: any) {
                    console.error('Failed to load products:', err);
                    showSnackbar('Failed to load products', 'error');
                }
            }
        };

        const fetchWarehouses = async () => {
            if (isAuthenticated) {
                try {
                    const response = await warehouseAPI.getWarehouses();
                    dispatch(setWarehouses(response.data));
                } catch (err: any) {
                    console.error('Failed to load warehouses:', err);
                    showSnackbar('Failed to load warehouses', 'error');
                }
            }
        };

        if (isAuthenticated) {
            fetchProducts();
            fetchWarehouses();
        }
    }, [isAuthenticated, dispatch]);

    // Initialize and connect to real-time sync
    useEffect(() => {
        if (isAuthenticated) {
            realTimeSyncService.connect();
            
            // Listen for real-time updates
            const handleInventoryUpdate = (data: any) => {
                if (data.type === 'inventory_update') {
                    switch (data.action) {
                        case 'create':
                            dispatch(addInventory(data.inventory));
                            break;
                        case 'update':
                            dispatch(updateInventory(data.inventory));
                            break;
                        case 'delete':
                            dispatch(deleteInventory(data.inventoryId));
                            break;
                    }
                }
            };

            // You'll need to implement this in your realTimeSyncService
            // realTimeSyncService.on('inventory_update', handleInventoryUpdate);

            return () => {
                // realTimeSyncService.off('inventory_update', handleInventoryUpdate);
                realTimeSyncService.disconnect();
            };
        }
    }, [isAuthenticated, dispatch]);

    const handleCreateInventory = () => {
        setEditingInventory(null);
        setIsFormOpen(true);
    };

    const handleEditInventory = (inventoryItem: Inventory) => {
        setEditingInventory(inventoryItem);
        setIsFormOpen(true);
    };

    // Helper function to handle inventory creation
    const handleCreateInventoryItem = async (inventoryData: any) => {
        try {
            const response = await inventoryAPI.createInventory(inventoryData);
            dispatch(addInventory(response.data));
            realTimeSyncService.sendInventoryUpdate('create', response.data);
            showSnackbar('Inventory item created successfully!', 'success');
            return response.data;
        } catch (err: any) {
            showSnackbar(err.message || 'Failed to create inventory', 'error');
            throw err;
        }
    };

    // Helper function to handle inventory update
    const handleUpdateInventoryItem = async (inventoryId: number, inventoryData: any) => {
        try {
            const response = await inventoryAPI.updateInventory(inventoryId, inventoryData);
            dispatch(updateInventory(response.data));
            realTimeSyncService.sendInventoryUpdate('update', response.data);
            showSnackbar('Inventory updated successfully!', 'success');
            return response.data;
        } catch (err: any) {
            showSnackbar(err.message || 'Failed to update inventory', 'error');
            throw err;
        }
    };

    // Helper function to handle inventory deletion
    const handleDeleteInventoryItem = async (inventoryId: number) => {
        try {
            await inventoryAPI.deleteInventory(inventoryId);
            dispatch(deleteInventory(inventoryId));
            realTimeSyncService.sendInventoryUpdate('delete', { id: inventoryId });
            showSnackbar('Inventory item deleted successfully!', 'success');
        } catch (err: any) {
            showSnackbar(err.message || 'Failed to delete inventory', 'error');
            throw err;
        }
    };

    const handleFormSubmit = async (inventoryData: any) => {
        try {
            if (editingInventory) {
                // Update existing inventory
                await handleUpdateInventoryItem(editingInventory.id, inventoryData);
            } else {
                // Add new inventory
                await handleCreateInventoryItem(inventoryData);
            }
            
            setIsFormOpen(false);
            setEditingInventory(null);
        } catch (err: any) {
            // Error is already handled in the helper functions
        }
    };

    const handleDeleteInventory = async (inventoryId: number) => {
        if (window.confirm('Are you sure you want to delete this inventory item?')) {
            try {
                await handleDeleteInventoryItem(inventoryId);
            } catch (err: any) {
                // Error is already handled in the helper function
            }
        }
    };

    const showSnackbar = (message: string, severity: 'success' | 'error') => {
        setSnackbar({ open: true, message, severity });
    };

    const handleCloseSnackbar = () => {
        setSnackbar({ ...snackbar, open: false });
    };

    // Filter inventory based on filter criteria
    const filteredInventory = inventory.filter(item => {
        if (filters.productId && item.product !== parseInt(filters.productId)) {
            return false;
        }
        if (filters.warehouseId && item.warehouse !== parseInt(filters.warehouseId)) {
            return false;
        }
        if (filters.binLocation && !item.bin_location?.toLowerCase().includes(filters.binLocation.toLowerCase())) {
            return false;
        }
        return true;
    });

    // Find product and warehouse names for display
    const getProductById = (id: number) => {
        return products.find(p => p.id === id);
    };

    const getWarehouseById = (id: number) => {
        return warehouses.find(w => w.id === id);
    };

    const getStockStatus = (qtyOnHand: number, minStockLevel: number) => {
        if (qtyOnHand === 0) return { status: 'Out of Stock', color: 'error' as const, severity: 'high' as const };
        if (qtyOnHand <= minStockLevel) return { status: 'Low Stock', color: 'warning' as const, severity: 'medium' as const };
        if (qtyOnHand <= minStockLevel * 2) return { status: 'Adequate', color: 'info' as const, severity: 'low' as const };
        return { status: 'In Stock', color: 'success' as const, severity: 'none' as const };
    };

    if (loading) {
        return (
            <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
                <CircularProgress />
            </Box>
        );
    }

    return (
        <Box sx={{ p: 3 }}>
            <Card>
                <CardHeader
                    title="Inventory Management"
                    action={
                        <PermissionGate permission="manage_inventory">
                            <Fab 
                                color="primary" 
                                aria-label="add inventory"
                                onClick={handleCreateInventory}
                                size="medium"
                            >
                                <AddIcon />
                            </Fab>
                        </PermissionGate>
                    }
                />
                <CardContent>
                    {error && (
                        <Alert severity="error" sx={{ mb: 2 }}>
                            {error}
                        </Alert>
                    )}

                    {/* Filters */}
                    <Box sx={{ mb: 3, p: 2, bgcolor: 'background.default', borderRadius: 1 }}>
                        <Grid container spacing={2}>
                            <Grid item xs={12} sm={4}>
                                <FormControl fullWidth>
                                    <InputLabel>Product</InputLabel>
                                    <Select
                                        value={filters.productId}
                                        label="Product"
                                        onChange={(e) => setFilters({...filters, productId: e.target.value})}
                                    >
                                        <MenuItem value="">All Products</MenuItem>
                                        {products.map(product => (
                                            <MenuItem key={product.id} value={product.id.toString()}>
                                                {product.name}
                                            </MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>
                            </Grid>
                            <Grid item xs={12} sm={4}>
                                <FormControl fullWidth>
                                    <InputLabel>Warehouse</InputLabel>
                                    <Select
                                        value={filters.warehouseId}
                                        label="Warehouse"
                                        onChange={(e) => setFilters({...filters, warehouseId: e.target.value})}
                                    >
                                        <MenuItem value="">All Warehouses</MenuItem>
                                        {warehouses.map(warehouse => (
                                            <MenuItem key={warehouse.id} value={warehouse.id.toString()}>
                                                {warehouse.name}
                                            </MenuItem>
                                        ))}
                                    </Select>
                                </FormControl>
                            </Grid>
                            <Grid item xs={12} sm={4}>
                                <TextField
                                    label="Bin/Location"
                                    type="text"
                                    fullWidth
                                    variant="outlined"
                                    value={filters.binLocation}
                                    onChange={(e) => setFilters({...filters, binLocation: e.target.value})}
                                    placeholder="Search by location..."
                                />
                            </Grid>
                        </Grid>
                    </Box>

                    <PermissionGate permission="view_inventory">
                        <Grid container spacing={3}>
                            {filteredInventory.map((inventoryItem) => {
                                const product = getProductById(inventoryItem.product);
                                const warehouse = getWarehouseById(inventoryItem.warehouse);
                                const stockStatus = getStockStatus(inventoryItem.qty_on_hand, inventoryItem.min_stock_level);
                                
                                return (
                                    <Grid item xs={12} sm={6} md={4} key={inventoryItem.id}>
                                        <Card 
                                            variant="outlined"
                                            sx={{ 
                                                height: '100%',
                                                borderColor: stockStatus.severity === 'high' ? 'error.main' : 
                                                           stockStatus.severity === 'medium' ? 'warning.main' : 'divider'
                                            }}
                                        >
                                            <CardContent>
                                                <Stack spacing={2}>
                                                    <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                                        <Box sx={{ flex: 1 }}>
                                                            <Typography variant="h6" component="h3" gutterBottom>
                                                                {product?.name || `Product #${inventoryItem.product}`}
                                                            </Typography>
                                                            <Typography variant="body2" color="text.secondary" gutterBottom>
                                                                SKU: {product?.sku || 'N/A'}
                                                            </Typography>
                                                        </Box>
                                                        <PermissionGate permission="manage_inventory">
                                                            <Box>
                                                                <IconButton 
                                                                    size="small" 
                                                                    onClick={() => handleEditInventory(inventoryItem)}
                                                                    color="primary"
                                                                >
                                                                    <EditIcon fontSize="small" />
                                                                </IconButton>
                                                                <IconButton 
                                                                    size="small" 
                                                                    onClick={() => handleDeleteInventory(inventoryItem.id)}
                                                                    color="error"
                                                                >
                                                                    <DeleteIcon fontSize="small" />
                                                                </IconButton>
                                                            </Box>
                                                        </PermissionGate>
                                                    </Box>

                                                    <Box>
                                                        <Typography variant="body2" gutterBottom>
                                                            <strong>Warehouse:</strong> {inventoryItem.warehouse_name || warehouse?.name || `Warehouse #${inventoryItem.warehouse}`}
                                                        </Typography>
                                                        {inventoryItem.location_name && (
                                                            <Typography variant="body2" gutterBottom>
                                                                <strong>Location:</strong> {inventoryItem.location_name}
                                                            </Typography>
                                                        )}
                                                        {inventoryItem.bin_name && (
                                                            <Typography variant="body2" gutterBottom>
                                                                <strong>Bin:</strong> {inventoryItem.bin_name}
                                                            </Typography>
                                                        )}
                                                        {inventoryItem.bin_location && !inventoryItem.location_name && (
                                                            <Typography variant="body2" gutterBottom>
                                                                <strong>Legacy Location:</strong> {inventoryItem.bin_location}
                                                            </Typography>
                                                        )}
                                                    </Box>

                                                    <Box>
                                                        <Stack direction="row" spacing={1} alignItems="center" mb={1}>
                                                            <Typography variant="h6" color="primary">
                                                                On Hand: {inventoryItem.qty_on_hand}
                                                            </Typography>
                                                            <Chip 
                                                                label={stockStatus.status}
                                                                color={stockStatus.color}
                                                                size="small"
                                                                variant={stockStatus.severity === 'high' ? 'filled' : 'outlined'}
                                                                icon={stockStatus.severity === 'high' ? <WarningIcon /> : undefined}
                                                            />
                                                        </Stack>
                                                        <Typography variant="body2" color="text.secondary">
                                                            Reserved: {inventoryItem.qty_reserved} | Min Stock: {inventoryItem.min_stock_level}
                                                        </Typography>
                                                    </Box>

                                                    {inventoryItem.last_updated && (
                                                        <Typography variant="caption" color="text.secondary">
                                                            Last updated: {new Date(inventoryItem.last_updated).toLocaleDateString()}
                                                        </Typography>
                                                    )}
                                                </Stack>
                                            </CardContent>
                                        </Card>
                                    </Grid>
                                );
                            })}
                        </Grid>
                        
                        {filteredInventory.length === 0 && (
                            <Box textAlign="center" py={4}>
                                <Typography variant="h6" color="text.secondary">
                                    {inventory.length === 0 ? 'No inventory items found' : 'No inventory items matching your filters'}
                                </Typography>
                            </Box>
                        )}
                    </PermissionGate>
                </CardContent>
            </Card>
            
            {/* Inventory Form Modal */}
            <PermissionGate permission="manage_inventory">
                <InventoryForm 
                    open={isFormOpen}
                    onClose={() => {
                        setIsFormOpen(false);
                        setEditingInventory(null);
                    }}
                    onSubmit={handleFormSubmit}
                    initialData={editingInventory}
                    products={products}
                    warehouses={warehouses}
                />
            </PermissionGate>

            {/* Snackbar for notifications */}
            <Snackbar
                open={snackbar.open}
                autoHideDuration={6000}
                onClose={handleCloseSnackbar}
                anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
            >
                <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
                    {snackbar.message}
                </Alert>
            </Snackbar>
        </Box>
    );
};

export default InventoryPage;