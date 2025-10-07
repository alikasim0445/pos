import React, { useState, useEffect } from 'react';
import { customerAPI } from '../services/api';
import { useAppSelector } from '../hooks/redux';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  CircularProgress,
  Alert,
  Grid,
  Chip,
  Divider,
} from '@mui/material';
import { format } from 'date-fns';

interface CustomerPurchaseHistory {
  id: number;
  name: string;
  email?: string;
  phone?: string;
}

interface SaleItem {
  product_name: string;
  quantity: number;
  unit_price: number;
  total_price: number;
}

interface Payment {
  method: string;
  amount: number;
  reference?: string;
}

interface SaleHistory {
  id: number;
  receipt_number: string;
  sale_date: string;
  total_amount: number;
  payment_status: string;
  items: SaleItem[];
  payments: Payment[];
}

interface CustomerHistoryProps {
  customerId: number;
}

const CustomerDetails: React.FC<CustomerHistoryProps> = ({ customerId }) => {
  const [customerData, setCustomerData] = useState<CustomerPurchaseHistory | null>(null);
  const [purchaseHistory, setPurchaseHistory] = useState<SaleHistory[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    const loadCustomerHistory = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await customerAPI.getCustomerPurchaseHistory(customerId);
        setCustomerData(response.data.customer);
        setPurchaseHistory(response.data.purchase_history);
      } catch (err: any) {
        setError(err.message || 'Failed to load customer purchase history');
        console.error('Error loading customer purchase history:', err);
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated && customerId) {
      loadCustomerHistory();
    }
  }, [customerId, isAuthenticated]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error}
      </Alert>
    );
  }

  return (
    <Box>
      {customerData && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Typography variant="h5" component="div" gutterBottom>
              Customer Information
            </Typography>
            <Typography variant="h6">{customerData.name}</Typography>
            {customerData.email && (
              <Typography color="textSecondary">Email: {customerData.email}</Typography>
            )}
            {customerData.phone && (
              <Typography color="textSecondary">Phone: {customerData.phone}</Typography>
            )}
            <Typography variant="subtitle1" sx={{ mt: 2 }}>
              Purchase Summary
            </Typography>
            <Typography>Total Orders: {purchaseHistory.length}</Typography>
            <Typography>
              Total Spent: ${purchaseHistory.reduce((sum, sale) => sum + sale.total_amount, 0).toFixed(2)}
            </Typography>
          </CardContent>
        </Card>
      )}

      <Typography variant="h5" sx={{ mb: 2 }}>
        Purchase History
      </Typography>

      {purchaseHistory.length === 0 ? (
        <Typography>No purchase history available.</Typography>
      ) : (
        <Grid container spacing={3}>
          {purchaseHistory.map((sale) => (
            <Grid item xs={12} key={sale.id}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                    <Typography variant="h6">Receipt: {sale.receipt_number}</Typography>
                    <Box>
                      <Chip
                        label={sale.payment_status}
                        color={
                          sale.payment_status === 'completed' ? 'success' :
                          sale.payment_status === 'pending' ? 'warning' :
                          sale.payment_status === 'cancelled' ? 'error' : 'default'
                        }
                        size="small"
                      />
                      <Typography variant="body2" color="textSecondary" sx={{ mt: 1 }}>
                        Date: {format(new Date(sale.sale_date), 'MMM dd, yyyy HH:mm')}
                      </Typography>
                    </Box>
                  </Box>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Typography variant="subtitle1" gutterBottom>
                    Items:
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Product</TableCell>
                          <TableCell align="right">Qty</TableCell>
                          <TableCell align="right">Unit Price</TableCell>
                          <TableCell align="right">Total</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {sale.items.map((item, idx) => (
                          <TableRow key={idx}>
                            <TableCell>{item.product_name}</TableCell>
                            <TableCell align="right">{item.quantity}</TableCell>
                            <TableCell align="right">${item.unit_price.toFixed(2)}</TableCell>
                            <TableCell align="right">${item.total_price.toFixed(2)}</TableCell>
                          </TableRow>
                        ))}
                        <TableRow>
                          <TableCell colSpan={3} align="right"><strong>Total Amount:</strong></TableCell>
                          <TableCell align="right"><strong>${sale.total_amount.toFixed(2)}</strong></TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                  
                  <Divider sx={{ my: 2 }} />
                  
                  <Typography variant="subtitle1" gutterBottom>
                    Payments:
                  </Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Method</TableCell>
                          <TableCell align="right">Amount</TableCell>
                          <TableCell>Reference</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {sale.payments.map((payment, idx) => (
                          <TableRow key={idx}>
                            <TableCell>
                              <Chip 
                                label={payment.method} 
                                size="small" 
                                variant="outlined" 
                              />
                            </TableCell>
                            <TableCell align="right">${payment.amount.toFixed(2)}</TableCell>
                            <TableCell>{payment.reference || '-'}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </Box>
  );
};

export default CustomerDetails;