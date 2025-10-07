import React, { useState, useEffect } from 'react';
import { useAppSelector } from '../hooks/redux';
import { productAPI, saleAPI, warehouseAPI } from '../services/api';
import ProductList from './ProductList';
import WarehouseSelector from './WarehouseSelector';
import ReceiptPreview from './ReceiptPreview';
import BarcodeScanner from './BarcodeScanner';
import offlineStorage from '../utils/offlineStorage';
import {
  Button,
  Typography,
  Box,
  Alert,
  Dialog,
  DialogContent,
} from '@mui/material';
import { Scanner as ScannerIcon } from '@mui/icons-material';

const POSTerminal: React.FC = () => {
    const [products, setProducts] = useState([]);
    const [warehouses, setWarehouses] = useState([]);
    const [selectedProducts, setSelectedProducts] = useState([]);
    const [warehouseId, setWarehouseId] = useState<number | null>(null);
    const [total, setTotal] = useState(0);
    const [error, setError] = useState<string | null>(null);
    const [receiptData, setReceiptData] = useState<any>(null);
    const [showReceipt, setShowReceipt] = useState(false);
    const [showScanner, setShowScanner] = useState(false);
    const [isOnline, setIsOnline] = useState(navigator.onLine);
    const { isAuthenticated, user } = useAppSelector((state) => state.auth);

    useEffect(() => {
        // Handle online/offline status
        const handleOnline = () => setIsOnline(true);
        const handleOffline = () => setIsOnline(false);

        window.addEventListener('online', handleOnline);
        window.addEventListener('offline', handleOffline);

        const loadProducts = async () => {
            try {
                const response = await productAPI.getProducts();
                setProducts(response.data);
                
                // Save products for offline use
                await offlineStorage.saveProductsForOffline(response.data);
            } catch (err: any) {
                // Try to load from offline storage if API call fails
                try {
                    const offlineProducts = await offlineStorage.getProductsForOffline();
                    setProducts(offlineProducts);
                    console.warn('Loaded products from offline storage');
                } catch (offlineErr) {
                    console.error('Could not load from offline storage:', offlineErr);
                }
                console.error('Error loading products:', err);
                setError(err.message || 'Failed to load products');
            }
        };

        const loadWarehouses = async () => {
            try {
                const response = await warehouseAPI.getWarehouses();
                setWarehouses(response.data);
            } catch (err: any) {
                setError(err.message || 'Failed to load warehouses');
            }
        };

        if (isAuthenticated) {
            loadProducts();
            loadWarehouses();
        }

        // Cleanup event listeners
        return () => {
            window.removeEventListener('online', handleOnline);
            window.removeEventListener('offline', handleOffline);
        };
    }, [isAuthenticated]);

    const handleProductSelect = (product: any) => {
        setSelectedProducts((prev: any[]) => [...prev, product]);
        setTotal((prev) => prev + parseFloat(product.price));
    };

    const handleSaleProcess = async () => {
        if (!warehouseId || selectedProducts.length === 0) {
            alert('Please select a warehouse and at least one product.');
            return;
        }

        if (!user) {
            setError('User not authenticated');
            return;
        }

        try {
            // Prepare sale data
            const saleData = {
                cashier_id: user.id, // Use the authenticated user's ID
                customer_id: null, // Optional - could be added later
                warehouse_id: warehouseId,
                items: selectedProducts.map((product: any) => ({
                    product_id: product.id,
                    variant_id: null, // Could be added if variants are used
                    quantity: 1, // For now, default to 1 - could be extended with quantity selector
                    unit_price: parseFloat(product.price),
                })),
                payments: [
                    {
                        method: 'cash', // Default payment method - could be selected by user
                        amount: total,
                    }
                ]
            };

            // Process the sale and get the response
            const response = await saleAPI.createSale(saleData);
            const newSale = response.data;
            
            // Set the receipt data and show the receipt
            setReceiptData(newSale);
            setShowReceipt(true);
            
            // Reset state after processing sale
            setSelectedProducts([]);
            setTotal(0);
        } catch (err: any) {
            setError(err.message || 'Failed to process sale');
        }
    };

    const handleScan = async (barcodeData: string) => {
        try {
            // Find the product by barcode
            const foundProduct = products.find((product: any) => 
                product.barcode === barcodeData
            );
            
            if (foundProduct) {
                // Add the product to selected products
                setSelectedProducts((prev: any[]) => [...prev, foundProduct]);
                setTotal((prev) => prev + parseFloat(foundProduct.price));
                setShowScanner(false);
            } else {
                setError('Product not found with this barcode');
            }
        } catch (err: any) {
            setError(err.message || 'Error scanning product');
        }
    };

    const handleError = (error: Error) => {
        setError(error.message || 'Error scanning barcode');
        setShowScanner(false);
    };

    return (
        <div className="mb-8">
            <h1 className="text-2xl font-bold text-gray-800 mb-6">Point of Sale Terminal</h1>
            
            {error && (
                <Alert severity="error" sx={{ mb: 2 }}>
                    {error}
                </Alert>
            )}
            
            <div className="mb-6">
                <WarehouseSelector 
                    warehouses={warehouses} 
                    onSelect={(id: number) => setWarehouseId(id)} 
                />
            </div>
            
            <div className="mb-6">
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">Products</Typography>
                    <Button 
                        variant="outlined" 
                        startIcon={<ScannerIcon />}
                        onClick={() => setShowScanner(true)}
                    >
                        Scan Barcode
                    </Button>
                </Box>
                <ProductList 
                    products={products} 
                    onSelect={handleProductSelect} 
                />
            </div>
            
            <div className="mb-6 p-4 bg-gray-100 rounded-lg">
                <Typography variant="h6">
                    Total: <span className="text-green-600">${total.toFixed(2)}</span>
                </Typography>
            </div>
            
            <Button 
                onClick={handleSaleProcess}
                variant="contained"
                color="primary"
                disabled={!warehouseId || selectedProducts.length === 0}
            >
                Process Sale
            </Button>
            
            {/* Barcode Scanner Dialog */}
            <BarcodeScanner
                open={showScanner}
                onClose={() => setShowScanner(false)}
                onScan={handleScan}
                onError={handleError}
            />
            
            {/* Receipt Preview Dialog */}
            <Dialog 
                open={showReceipt} 
                onClose={() => setShowReceipt(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogContent>
                    {receiptData && (
                        <ReceiptPreview 
                            sale={receiptData} 
                            onPrint={() => {
                                // Print functionality
                                setTimeout(() => {
                                    window.print();
                                }, 500);
                            }}
                        />
                    )}
                </DialogContent>
            </Dialog>
        </div>
    );
};

export default POSTerminal;