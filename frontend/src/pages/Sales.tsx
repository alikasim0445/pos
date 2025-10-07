import React, { useEffect, useState } from 'react';
import { useAppSelector } from '../hooks/redux';
import { saleAPI } from '../services/api';
import POSTerminal from '../components/POSTerminal';
import ReceiptPreview from '../components/ReceiptPreview';
import ReturnForm from '../components/ReturnForm';
import ReturnList from '../components/ReturnList';
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
} from '@mui/material';
import { Add as AddIcon, Print as PrintIcon, Undo as UndoIcon } from '@mui/icons-material';

const Sales: React.FC = () => {
    const [salesData, setSalesData] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [selectedReceipt, setSelectedReceipt] = useState<any>(null);
    const [showReceiptDialog, setShowReceiptDialog] = useState(false);
    const [activeTab, setActiveTab] = useState(0);
    const [showReturnForm, setShowReturnForm] = useState(false);
    const [selectedSaleIdForReturn, setSelectedSaleIdForReturn] = useState<number | null>(null);
    const { isAuthenticated } = useAppSelector((state) => state.auth);

    useEffect(() => {
        const loadSalesData = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await saleAPI.getSales();
                setSalesData(response.data);
            } catch (err: any) {
                setError(err.message || 'Failed to load sales data');
                console.error('Error fetching sales data:', err);
            } finally {
                setLoading(false);
            }
        };

        if (isAuthenticated) {
            loadSalesData();
        }
    }, [isAuthenticated, activeTab]);

    const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
        setActiveTab(newValue);
    };

    const handleProcessReturn = (saleId: number) => {
        setSelectedSaleIdForReturn(saleId);
        setShowReturnForm(true);
    };

    if (loading && activeTab === 0) {
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
            <h1 className="text-3xl font-bold text-gray-800 mb-6">Sales Management</h1>
            
            <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 3 }}>
                <Tab label="POS Terminal" />
                <Tab label="Sales History" />
                <Tab label="Returns & Exchanges" />
            </Tabs>
            
            {activeTab === 0 && (
                <div className="bg-white rounded-lg shadow-md p-6 mb-6">
                    <POSTerminal />
                </div>
            )}
            
            {activeTab === 1 && (
                <div>
                    <Grid container spacing={3}>
                        {salesData.map((sale: any) => (
                            <Grid item xs={12} sm={6} md={4} key={sale.id}>
                                <Card>
                                    <CardContent>
                                        <Typography variant="h6" component="h2">
                                            Receipt: {sale.receipt_number}
                                        </Typography>
                                        <Typography>
                                            Date: {new Date(sale.sale_date).toLocaleDateString()}
                                        </Typography>
                                        <Typography>
                                            Amount: ${sale.total_amount}
                                        </Typography>
                                        <Typography>
                                            Status: {sale.payment_status}
                                        </Typography>
                                        <Box mt={2} display="flex" justifyContent="space-between">
                                            <Button
                                                variant="contained"
                                                color="primary"
                                                size="small"
                                                startIcon={<PrintIcon />}
                                                onClick={async () => {
                                                    try {
                                                        const response = await saleAPI.getSaleById(sale.id);
                                                        setSelectedReceipt(response.data);
                                                        setShowReceiptDialog(true);
                                                    } catch (error) {
                                                        console.error('Error loading receipt data:', error);
                                                        setError('Failed to load receipt data');
                                                    }
                                                }}
                                            >
                                                Print
                                            </Button>
                                            <Button
                                                variant="outlined"
                                                color="secondary"
                                                size="small"
                                                startIcon={<UndoIcon />}
                                                onClick={() => handleProcessReturn(sale.id)}
                                            >
                                                Return
                                            </Button>
                                        </Box>
                                    </CardContent>
                                </Card>
                            </Grid>
                        ))}
                    </Grid>
                </div>
            )}
            
            {activeTab === 2 && (
                <ReturnList />
            )}
            
            {/* Add Sale Floating Action Button - only show in POS tab */}
            {activeTab === 0 && (
                <Fab 
                    color="primary" 
                    aria-label="add" 
                    style={{ position: 'fixed', bottom: 16, right: 16 }}
                >
                    <AddIcon />
                </Fab>
            )}
            
            {/* Receipt Preview Dialog */}
            <Dialog 
                open={showReceiptDialog} 
                onClose={() => setShowReceiptDialog(false)}
                maxWidth="sm"
                fullWidth
            >
                <DialogContent>
                    {selectedReceipt && (
                        <ReceiptPreview 
                            sale={selectedReceipt} 
                            onPrint={() => {
                                // Print functionality
                                setTimeout(() => {
                                    window.print();
                                }, 500);
                            }}
                            onDownload={async () => {
                                try {
                                    const response = await saleAPI.downloadReceipt(selectedReceipt.id);
                                    // Create a blob from the response data
                                    const blob = new Blob([response.data], { type: 'application/pdf' });
                                    // Create a download link
                                    const downloadUrl = window.URL.createObjectURL(blob);
                                    const link = document.createElement('a');
                                    link.href = downloadUrl;
                                    link.setAttribute('download', `receipt_${selectedReceipt.receipt_number}.pdf`);
                                    document.body.appendChild(link);
                                    link.click();
                                    link.remove();
                                    setShowReceiptDialog(false);
                                } catch (error) {
                                    console.error('Error downloading receipt:', error);
                                    setError('Failed to download receipt');
                                }
                            }}
                        />
                    )}
                </DialogContent>
            </Dialog>
            
            {/* Return Form Dialog */}
            <Dialog 
                open={showReturnForm} 
                onClose={() => setShowReturnForm(false)}
                maxWidth="md"
                fullWidth
            >
                {selectedSaleIdForReturn && (
                    <ReturnForm 
                        open={showReturnForm} 
                        onClose={() => setShowReturnForm(false)}
                        saleId={selectedSaleIdForReturn}
                    />
                )}
            </Dialog>
        </div>
    );
};

export default Sales;