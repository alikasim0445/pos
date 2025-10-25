import React, { useState, useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import { productAPI, saleAPI, warehouseAPI, customerAPI, couponAPI } from '../services/api';
import { setProducts } from '../store/productsSlice';
import ProductList from './ProductList';
import WarehouseSelector from './WarehouseSelector';
import ReceiptPreview from './ReceiptPreview';
import BarcodeScanner from './BarcodeScanner';
import offlineStorage from '../utils/offlineStorage';
import realTimeSyncService from '../services/realTimeSyncService';
import {
  Button,
  Typography,
  Box,
  Alert,
  Dialog,
  DialogContent,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  IconButton,
  InputAdornment,
  Chip,
} from '@mui/material';
import { Scanner as ScannerIcon, Delete as DeleteIcon } from '@mui/icons-material';

interface SelectedProduct {
  id: number;
  name: string;
  price: string;
  quantity: number;
  barcode?: string | null;
}

const POSTerminal: React.FC = () => {
  const dispatch = useAppDispatch();
  const { products } = useAppSelector((state) => state.products);
  const [warehouses, setWarehouses] = useState<any[]>([]);
  const [customers, setCustomers] = useState<any[]>([]);
  const [selectedProducts, setSelectedProducts] = useState<SelectedProduct[]>([]);
  const [warehouseId, setWarehouseId] = useState<number | null>(null);
  const [customerId, setCustomerId] = useState<number | null>(null);
  const [total, setTotal] = useState(0);
  const [subTotal, setSubTotal] = useState(0);
  const [tax, setTax] = useState(0);
  const [discount, setDiscount] = useState(0);
  const [couponCode, setCouponCode] = useState('');
  const [appliedCoupon, setAppliedCoupon] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [receiptData, setReceiptData] = useState<any>(null);
  const [showReceipt, setShowReceipt] = useState(false);
  const [showScanner, setShowScanner] = useState(false);
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [paymentMethod, setPaymentMethod] = useState('cash');
  const [amountTendered, setAmountTendered] = useState(0);
  const [change, setChange] = useState(0);
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);

  useEffect(() => {
    // Handle online/offline status
    const handleOnline = async () => {
      setIsOnline(true);
      // Trigger background sync when back online
      if ('serviceWorker' in navigator && 'sync' in navigator.serviceWorker) {
        try {
          await navigator.serviceWorker.ready;
          await (navigator.serviceWorker as any).sync.register('sync-transactions');
          console.log('Background sync registered for offline transactions');
        } catch (err) {
          console.error('Background sync registration failed:', err);
        }
      }
    };
    
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    const loadProducts = async () => {
      try {
        const response = await productAPI.getProducts();
        dispatch(setProducts(response.data));
        
        // Save products for offline use
        await offlineStorage.saveProductsForOffline(response.data);
      } catch (err: any) {
        // Try to load from offline storage if API call fails
        try {
          const offlineProducts = await offlineStorage.getProductsForOffline();
          dispatch(setProducts(offlineProducts));
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

    const loadCustomers = async () => {
      try {
        const response = await customerAPI.getCustomers();
        setCustomers(response.data);
      } catch (err: any) {
        console.error('Error loading customers:', err);
      }
    };

    if (isAuthenticated) {
      loadProducts();
      loadWarehouses();
      loadCustomers();
    }

    // Initialize and connect to real-time sync
    realTimeSyncService.connect();

    // Cleanup event listeners
    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
      realTimeSyncService.disconnect();
    };
  }, [isAuthenticated, dispatch]);

  // Calculate totals when selected products change
  useEffect(() => {
    const subTotalValue = selectedProducts.reduce((sum, product) => {
      const quantity = product.quantity || 1;
      return sum + (parseFloat(product.price) * quantity);
    }, 0);
    
    setSubTotal(subTotalValue);
    
    // Calculate tax (assuming 10% for now)
    const calculatedTax = subTotalValue * 0.1;
    setTax(calculatedTax);
    
    // Calculate total
    let totalValue = subTotalValue + calculatedTax;
    
    // Apply discount if coupon is applied
    if (appliedCoupon) {
      if (appliedCoupon.coupon_type === 'percentage') {
        // Percentage discount
        const discountAmount = totalValue * (appliedCoupon.discount_value / 100);
        setDiscount(discountAmount);
        totalValue = totalValue - discountAmount;
      } else if (appliedCoupon.coupon_type === 'fixed_amount') {
        // Fixed amount discount
        const discountAmount = Math.min(appliedCoupon.discount_value, totalValue);
        setDiscount(discountAmount);
        totalValue = totalValue - discountAmount;
      }
    } else {
      setDiscount(0);
    }
    
    setTotal(totalValue);
    
    // Calculate change
    const calculatedChange = Math.max(0, amountTendered - totalValue);
    setChange(calculatedChange);
  }, [selectedProducts, appliedCoupon, amountTendered]);

  const handleProductSelect = (product: any) => {
    // Check if product is already in the list
    const existingIndex = selectedProducts.findIndex(p => p.id === product.id);
    
    if (existingIndex >= 0) {
      // If product already exists, increase quantity
      const updatedProducts = [...selectedProducts];
      updatedProducts[existingIndex] = {
        ...updatedProducts[existingIndex],
        quantity: updatedProducts[existingIndex].quantity + 1
      };
      setSelectedProducts(updatedProducts);
    } else {
      // Add new product with quantity 1
      setSelectedProducts((prev: SelectedProduct[]) => [
        ...prev,
        {
          id: product.id,
          name: product.name,
          price: product.price.toString(),
          quantity: 1,
          barcode: product.barcode
        }
      ]);
    }
  };

  const updateProductQuantity = (index: number, newQuantity: number) => {
    if (newQuantity < 1) return;
    
    const updatedProducts = [...selectedProducts];
    updatedProducts[index] = {
      ...updatedProducts[index],
      quantity: newQuantity
    };
    setSelectedProducts(updatedProducts);
  };

  const removeProduct = (index: number) => {
    const updatedProducts = [...selectedProducts];
    updatedProducts.splice(index, 1);
    setSelectedProducts(updatedProducts);
  };

  const applyCoupon = async () => {
    if (!couponCode.trim()) {
      setError('Please enter a coupon code');
      return;
    }

    try {
      // Check if the coupon exists and is valid
      const response = await couponAPI.verifyCoupon(couponCode);
      const couponData = response.data;
      
      if (!couponData.is_valid) {
        setError('This coupon is not valid');
        return;
      }

      setAppliedCoupon(couponData);
      setCouponCode('');
      setError(null);
    } catch (err: any) {
      setError(err.message || 'Invalid coupon code');
    }
  };

  const removeCoupon = () => {
    setAppliedCoupon(null);
    setDiscount(0);
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

    // Validate payment
    if (paymentMethod === 'cash' && amountTendered < total) {
      setError('Amount tendered is less than the total amount');
      return;
    }

    try {
      // Prepare sale data
      const saleData = {
        cashier_id: user.id,
        customer_id: customerId,
        warehouse_id: warehouseId,
        items: selectedProducts.map((product) => ({
          product_id: product.id,
          variant_id: null,
          quantity: product.quantity,
          unit_price: parseFloat(product.price),
        })),
        payments: [
          {
            method: paymentMethod,
            amount: total,
          }
        ],
        tax_amount: tax,
        discount_amount: discount,
        notes: appliedCoupon ? `Applied coupon: ${appliedCoupon.code}` : '',
      };

      // Process the sale and get the response
      const response = await saleAPI.createSale(saleData);
      const newSale = response.data;
      
      // Send real-time update for the new sale
      realTimeSyncService.sendSaleUpdate('create', newSale);
      
      // Set the receipt data and show the receipt
      setReceiptData(newSale);
      setShowReceipt(true);
      
      // Reset state after processing sale
      setSelectedProducts([]);
      setTotal(0);
      setSubTotal(0);
      setTax(0);
      setDiscount(0);
      setAmountTendered(0);
      setChange(0);
      setAppliedCoupon(null);
      setCouponCode('');
      setError(null);
    } catch (err: any) {
      // Check if the error is due to network connectivity
      if (!navigator.onLine || err.message.includes('Failed to fetch') || err.message.includes('Network Error')) {
        // Save the sale to offline storage and inform the user
        try {
          // Prepare offline sale data with timestamp
          const offlineSaleData = {
            ...saleData,
            timestamp: new Date().toISOString(),
          };
          
          await offlineStorage.saveOfflineSale(offlineSaleData);
          
          // Show success message with offline indicator
          alert('Sale saved offline. It will be synced when connection is restored.');
          
          // Set the receipt data and show the receipt for the offline sale
          setReceiptData({
            ...saleData,
            id: `offline-${Date.now()}`, // Temporary ID for display
            receipt_number: `OFFLINE-${Date.now()}`, // Temporary receipt number
            sale_date: new Date().toISOString(),
          });
          setShowReceipt(true);
          
          // Reset state after processing sale
          setSelectedProducts([]);
          setTotal(0);
          setSubTotal(0);
          setTax(0);
          setDiscount(0);
          setAmountTendered(0);
          setChange(0);
          setAppliedCoupon(null);
          setCouponCode('');
          setError(null);
        } catch (offlineErr: any) {
          setError(`Failed to save sale offline: ${offlineErr.message || 'Unknown error'}`);
        }
      } else {
        setError(err.message || 'Failed to process sale');
      }
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
        handleProductSelect(foundProduct);
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

  const handleAmountTenderedChange = (value: string) => {
    const amount = parseFloat(value) || 0;
    setAmountTendered(amount);
  };

  return (
    <div className="mb-8">
      <h1 className="text-2xl font-bold text-gray-800 mb-6">Point of Sale Terminal</h1>
      
      {error && (
        <Alert severity="error" sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}
      
      <Grid container spacing={3}>
        {/* Left Column - Products Section */}
        <Grid xs={12} md={8}>
          <div className="mb-6">
            <WarehouseSelector 
              warehouses={warehouses} 
              onSelect={(id: number) => setWarehouseId(id)} 
            />
          </div>
          
          <div className="mb-4">
            <FormControl fullWidth margin="normal">
              <InputLabel>Customer</InputLabel>
              <Select
                value={customerId || ''}
                onChange={(e) => setCustomerId(e.target.value as number)}
                label="Customer"
              >
                <MenuItem value="">Walk-in Customer</MenuItem>
                {customers.map((customer) => (
                  <MenuItem key={customer.id} value={customer.id}>
                    {customer.first_name} {customer.last_name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
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
          
          {/* Selected Products Table */}
          {selectedProducts.length > 0 && (
            <div className="mb-6">
              <Typography variant="h6" gutterBottom>Selected Items</Typography>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Product</TableCell>
                      <TableCell align="right">Price</TableCell>
                      <TableCell align="center">Qty</TableCell>
                      <TableCell align="right">Total</TableCell>
                      <TableCell align="center">Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {selectedProducts.map((product, index) => (
                      <TableRow key={`${product.id}-${index}`}>
                        <TableCell>{product.name}</TableCell>
                        <TableCell align="right">${parseFloat(product.price).toFixed(2)}</TableCell>
                        <TableCell align="center">
                          <TextField
                            type="number"
                            size="small"
                            value={product.quantity}
                            onChange={(e) => updateProductQuantity(index, parseInt(e.target.value) || 1)}
                            inputProps={{ min: 1 }}
                            sx={{ width: 80 }}
                          />
                        </TableCell>
                        <TableCell align="right">
                          ${(parseFloat(product.price) * product.quantity).toFixed(2)}
                        </TableCell>
                        <TableCell align="center">
                          <IconButton 
                            color="error" 
                            size="small"
                            onClick={() => removeProduct(index)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </div>
          )}
        </Grid>
        
        {/* Right Column - Payment Section */}
        <Grid xs={12} md={4}>
          <Paper elevation={3} className="p-4">
            <Typography variant="h6" gutterBottom>Payment Details</Typography>
            
            <div className="mb-3 p-3 bg-gray-50 rounded-lg">
              <Typography variant="body2">Subtotal: <strong>${subTotal.toFixed(2)}</strong></Typography>
              <Typography variant="body2">Tax: <strong>${tax.toFixed(2)}</strong></Typography>
              {appliedCoupon && (
                <Typography variant="body2">
                  Discount ({appliedCoupon.code}): <strong>-${discount.toFixed(2)}</strong>
                </Typography>
              )}
              <Typography variant="h4" className="mt-2">
                Total: <strong className="text-green-600">${total.toFixed(2)}</strong>
              </Typography>
            </div>
            
            {/* Coupon Section */}
            <div className="mb-3">
              <Box display="flex" alignItems="center" gap={1}>
                <TextField
                  fullWidth
                  label="Coupon Code"
                  value={couponCode}
                  onChange={(e) => setCouponCode(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && applyCoupon()}
                  disabled={!!appliedCoupon}
                  size="small"
                />
                {appliedCoupon ? (
                  <Button 
                    variant="outlined" 
                    color="error" 
                    size="small"
                    onClick={removeCoupon}
                  >
                    Remove
                  </Button>
                ) : (
                  <Button 
                    variant="contained" 
                    color="primary" 
                    size="small"
                    onClick={applyCoupon}
                  >
                    Apply
                  </Button>
                )}
              </Box>
              {appliedCoupon && (
                <Box mt={1} p={1} bgcolor="#e8f5e8" borderRadius={1}>
                  <Typography variant="body2" color="success.main">
                    Applied: {appliedCoupon.code} - {appliedCoupon.discount_value}
                    {appliedCoupon.coupon_type === 'percentage' ? '%' : ' (fixed)'}
                  </Typography>
                </Box>
              )}
            </div>
            
            <div className="mb-3">
              <FormControl fullWidth margin="normal">
                <InputLabel>Payment Method</InputLabel>
                <Select
                  value={paymentMethod}
                  onChange={(e) => setPaymentMethod(e.target.value as string)}
                  label="Payment Method"
                >
                  <MenuItem value="cash">Cash</MenuItem>
                  <MenuItem value="card">Card</MenuItem>
                  <MenuItem value="mobile">Mobile Payment</MenuItem>
                  <MenuItem value="voucher">Voucher</MenuItem>
                </Select>
              </FormControl>
            </div>
            
            {paymentMethod === 'cash' && (
              <div className="mb-3">
                <TextField
                  fullWidth
                  label="Amount Tendered"
                  type="number"
                  value={amountTendered}
                  onChange={(e) => handleAmountTenderedChange(e.target.value)}
                  InputProps={{
                    startAdornment: <InputAdornment position="start">$</InputAdornment>,
                  }}
                  margin="normal"
                />
                {change > 0 && (
                  <Typography variant="body2" color="success.main" className="mt-1">
                    Change: ${change.toFixed(2)}
                  </Typography>
                )}
              </div>
            )}
            
            <div className="mt-4">
              <Button 
                onClick={handleSaleProcess}
                variant="contained"
                color="primary"
                fullWidth
                size="large"
                disabled={!warehouseId || selectedProducts.length === 0 || total <= 0}
              >
                Process Sale
              </Button>
            </div>
          </Paper>
        </Grid>
      </Grid>
      
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