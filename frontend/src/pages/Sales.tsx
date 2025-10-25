import React, { useEffect, useState } from 'react';
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import { saleAPI } from '../services/api';
import POSTerminal from '../components/POSTerminal';
import ReceiptPreview from '../components/ReceiptPreview';
import ReturnForm from '../components/ReturnForm';
import ReturnList from '../components/ReturnList';
import PermissionGate from '../components/PermissionGate';
import { setSales, addSale, updateSale, deleteSale, setLoading, setError } from '../store/salesSlice';
import realTimeSyncService from '../services/realTimeSyncService';
import {
  CircularProgress,
  Alert,
  Fab,
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Box,
  Dialog,
  DialogContent,
  Tabs,
  Tab,
  Chip,
  Stack,
  CardHeader,
  Snackbar,
  Divider,
} from '@mui/material';
import { 
  Add as AddIcon, 
  Print as PrintIcon, 
  Undo as UndoIcon,
  Receipt as ReceiptIcon,
  History as HistoryIcon,
  SwapHoriz as ReturnIcon
} from '@mui/icons-material';
import { Sale } from '../types';

const Sales: React.FC = () => {
    const dispatch = useAppDispatch();
    const { sales, loading, error } = useAppSelector((state) => state.sales);
    const [selectedReceipt, setSelectedReceipt] = useState<Sale | null>(null);
    const [showReceiptDialog, setShowReceiptDialog] = useState(false);
    const [activeTab, setActiveTab] = useState(0);
    const [showReturnForm, setShowReturnForm] = useState(false);
    const [selectedSaleIdForReturn, setSelectedSaleIdForReturn] = useState<number | null>(null);
    const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' });
    const { isAuthenticated } = useAppSelector((state) => state.auth);

    useEffect(() => {
        const loadSalesData = async () => {
            dispatch(setLoading(true));
            dispatch(setError(null));
            
            try {
                const response = await saleAPI.getSales();
                dispatch(setSales(response.data));
            } catch (err: any) {
                const errorMessage = err.message || 'Failed to load sales data';
                dispatch(setError(errorMessage));
                showSnackbar(errorMessage, 'error');
                console.error('Error fetching sales data:', err);
            } finally {
                dispatch(setLoading(false));
            }
        };

        if (isAuthenticated) {
            loadSalesData();
        }
    }, [isAuthenticated, dispatch]);

    // Initialize and connect to real-time sync
    useEffect(() => {
        if (isAuthenticated) {
            realTimeSyncService.connect();
            
            // Listen for real-time updates
            const handleSaleUpdate = (data: any) => {
                if (data.type === 'sale_update') {
                    switch (data.action) {
                        case 'create':
                            dispatch(addSale(data.sale));
                            break;
                        case 'update':
                            dispatch(updateSale(data.sale));
                            break;
                        case 'delete':
                            dispatch(deleteSale(data.saleId));
                            break;
                    }
                }
            };

            // You'll need to implement this in your realTimeSyncService
            // realTimeSyncService.on('sale_update', handleSaleUpdate);

            return () => {
                // realTimeSyncService.off('sale_update', handleSaleUpdate);
                realTimeSyncService.disconnect();
            };
        }
    }, [isAuthenticated, dispatch]);

    const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
        setActiveTab(newValue);
    };

    const handleProcessReturn = (saleId: number) => {
        setSelectedSaleIdForReturn(saleId);
        setShowReturnForm(true);
    };

    const handleViewReceipt = async (saleId: number) => {
        try {
            const response = await saleAPI.getSaleById(saleId);
            setSelectedReceipt(response.data);
            setShowReceiptDialog(true);
        } catch (error: any) {
            const errorMessage = error.message || 'Failed to load receipt data';
            showSnackbar(errorMessage, 'error');
            console.error('Error loading receipt data:', error);
        }
    };

    const handleDownloadReceipt = async (saleId: number) => {
        try {
            const response = await saleAPI.downloadReceipt(saleId);
            const blob = new Blob([response.data], { type: 'application/pdf' });
            const downloadUrl = window.URL.createObjectURL(blob);
            const link = document.createElement('a');
            link.href = downloadUrl;
            link.setAttribute('download', `receipt_${selectedReceipt?.receipt_number || saleId}.pdf`);
            document.body.appendChild(link);
            link.click();
            link.remove();
            window.URL.revokeObjectURL(downloadUrl);
            setShowReceiptDialog(false);
            showSnackbar('Receipt downloaded successfully!', 'success');
        } catch (error: any) {
            const errorMessage = error.message || 'Failed to download receipt';
            showSnackbar(errorMessage, 'error');
            console.error('Error downloading receipt:', error);
        }
    };

    const showSnackbar = (message: string, severity: 'success' | 'error') => {
        setSnackbar({ open: true, message, severity });
    };

    const handleCloseSnackbar = () => {
        setSnackbar({ ...snackbar, open: false });
    };

    const getPaymentStatusColor = (status: string) => {
        switch (status?.toLowerCase()) {
            case 'completed':
            case 'paid':
                return 'success';
            case 'pending':
                return 'warning';
            case 'failed':
            case 'cancelled':
                return 'error';
            case 'refunded':
                return 'info';
            default:
                return 'default';
        }
    };

    const formatCurrency = (amount: number) => {
        return new Intl.NumberFormat('en-US', {
            style: 'currency',
            currency: 'USD',
        }).format(amount);
    };

    const renderLoadingState = () => (
        <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
            <CircularProgress />
        </Box>
    );

    const renderErrorState = () => (
        <Alert severity="error" sx={{ mb: 2 }}>
            {error}
        </Alert>
    );

    if (loading && activeTab === 0) {
        return renderLoadingState();
    }

    return (
        <Box sx={{ p: 3 }}>
            <Card>
                <CardHeader
                    title="Sales Management"
                    titleTypographyProps={{ variant: 'h4', component: 'h1' }}
                />
                <CardContent>
                    {error && renderErrorState()}

                    <Tabs 
                        value={activeTab} 
                        onChange={handleTabChange} 
                        sx={{ mb: 3 }}
                        variant="fullWidth"
                    >
                        <Tab 
                            icon={<ReceiptIcon />} 
                            label="POS Terminal" 
                            iconPosition="start" 
                        />
                        <Tab 
                            icon={<HistoryIcon />} 
                            label="Sales History" 
                            iconPosition="start" 
                        />
                        <Tab 
                            icon={<ReturnIcon />} 
                            label="Returns & Exchanges" 
                            iconPosition="start" 
                        />
                    </Tabs>
                    
                    {activeTab === 0 && (
                        <PermissionGate permission="add_sale">
                            <POSTerminal />
                        </PermissionGate>
                    )}
                    
                    {activeTab === 1 && (
                        <PermissionGate permission="view_sale">
                            <Box>
                                {loading ? (
                                    renderLoadingState()
                                ) : (
                                    <Grid container spacing={3}>
                                        {sales.length === 0 ? (
                                            <Grid item xs={12}>
                                                <Box textAlign="center" py={4}>
                                                    <Typography variant="h6" color="text.secondary">
                                                        No sales found
                                                    </Typography>
                                                    <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                                                        Start making sales using the POS Terminal tab
                                                    </Typography>
                                                </Box>
                                            </Grid>
                                        ) : (
                                            sales.map((sale: Sale) => (
                                                <Grid item xs={12} sm={6} md={4} key={sale.id}>
                                                    <Card variant="outlined">
                                                        <CardContent>
                                                            <Stack spacing={2}>
                                                                <Box display="flex" justifyContent="space-between" alignItems="flex-start">
                                                                    <Typography variant="h6" component="h2">
                                                                        {sale.receipt_number}
                                                                    </Typography>
                                                                    <Chip 
                                                                        label={sale.payment_status}
                                                                        color={getPaymentStatusColor(sale.payment_status)}
                                                                        size="small"
                                                                    />
                                                                </Box>
                                                                
                                                                <Divider />
                                                                
                                                                <Box>
                                                                    <Typography variant="body2" color="text.secondary">
                                                                        Date: {new Date(sale.sale_date).toLocaleDateString()}
                                                                    </Typography>
                                                                    <Typography variant="body2" color="text.secondary">
                                                                        Time: {new Date(sale.sale_date).toLocaleTimeString()}
                                                                    </Typography>
                                                                </Box>
                                                                
                                                                <Box>
                                                                    <Typography variant="h6" color="primary">
                                                                        {formatCurrency(sale.total_amount)}
                                                                    </Typography>
                                                                    {sale.tax_amount > 0 && (
                                                                        <Typography variant="body2" color="text.secondary">
                                                                            Tax: {formatCurrency(sale.tax_amount)}
                                                                        </Typography>
                                                                    )}
                                                                    {sale.discount_amount > 0 && (
                                                                        <Typography variant="body2" color="text.secondary">
                                                                            Discount: {formatCurrency(sale.discount_amount)}
                                                                        </Typography>
                                                                    )}
                                                                </Box>

                                                                <Stack direction="row" spacing={1}>
                                                                    <Button
                                                                        variant="outlined"
                                                                        size="small"
                                                                        startIcon={<PrintIcon />}
                                                                        onClick={() => handleViewReceipt(sale.id)}
                                                                        fullWidth
                                                                    >
                                                                        Receipt
                                                                    </Button>
                                                                    <Button
                                                                        variant="outlined"
                                                                        color="secondary"
                                                                        size="small"
                                                                        startIcon={<UndoIcon />}
                                                                        onClick={() => handleProcessReturn(sale.id)}
                                                                        fullWidth
                                                                    >
                                                                        Return
                                                                    </Button>
                                                                </Stack>
                                                            </Stack>
                                                        </CardContent>
                                                    </Card>
                                                </Grid>
                                            ))
                                        )}
                                    </Grid>
                                )}
                            </Box>
                        </PermissionGate>
                    )}
                    
                    {activeTab === 2 && (
                        <PermissionGate permission="view_return">
                            <ReturnList />
                        </PermissionGate>
                    )}
                </CardContent>
            </Card>
            
            {/* Add Sale Floating Action Button - only show in POS tab */}
            {activeTab === 0 && (
                <PermissionGate permission="add_sale">
                    <Fab 
                        color="primary" 
                        aria-label="new sale"
                        sx={{ position: 'fixed', bottom: 16, right: 16 }}
                    >
                        <AddIcon />
                    </Fab>
                </PermissionGate>
            )}
            
            {/* Receipt Preview Dialog */}
            <Dialog 
                open={showReceiptDialog} 
                onClose={() => setShowReceiptDialog(false)}
                maxWidth="md"
                fullWidth
            >
                <DialogContent>
                    {selectedReceipt && (
                        <ReceiptPreview 
                            sale={selectedReceipt} 
                            onPrint={() => {
                                setTimeout(() => {
                                    window.print();
                                }, 500);
                            }}
                            onDownload={() => handleDownloadReceipt(selectedReceipt.id)}
                        />
                    )}
                </DialogContent>
            </Dialog>
            
            {/* Return Form Dialog */}
            <Dialog 
                open={showReturnForm} 
                onClose={() => {
                    setShowReturnForm(false);
                    setSelectedSaleIdForReturn(null);
                }}
                maxWidth="md"
                fullWidth
            >
                {selectedSaleIdForReturn && (
                    <ReturnForm 
                        open={showReturnForm} 
                        onClose={() => {
                            setShowReturnForm(false);
                            setSelectedSaleIdForReturn(null);
                        }}
                        saleId={selectedSaleIdForReturn}
                        onSuccess={() => {
                            setShowReturnForm(false);
                            setSelectedSaleIdForReturn(null);
                            showSnackbar('Return processed successfully!', 'success');
                        }}
                    />
                )}
            </Dialog>

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

export default Sales;