import React, { useState, useEffect } from 'react';
import { reportAPI } from '../services/api';
import { useAppSelector } from '../hooks/redux';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';

interface SaleReportItem {
  id: number;
  receipt_number: string;
  sale_date: string;
  customer_name: string;
  warehouse_name: string;
  total_amount: number;
  payment_status: string;
  items: Array<{
    product_name: string;
    quantity: number;
    unit_price: number;
    total_price: number;
  }>;
}

interface SalesReportProps {
  filters: {
    startDate: string;
    endDate: string;
    warehouseId: string;
    categoryId: string;
  };
}

const SalesReport: React.FC<SalesReportProps> = ({ filters }) => {
  const [reportData, setReportData] = useState<SaleReportItem[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const params: any = {};
        if (filters.startDate) params.start_date = filters.startDate;
        if (filters.endDate) params.end_date = filters.endDate;
        if (filters.warehouseId) params.warehouse_id = filters.warehouseId;
        
        const response = await reportAPI.getSalesReport(params);
        setReportData(response.data.sales);
        setSummary(response.data.summary);
      } catch (err: any) {
        setError(err.message || 'Failed to load sales report');
        console.error('Error loading sales report:', err);
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchReport();
    }
  }, [filters, isAuthenticated]);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <Box mb={3}>
        <Typography variant="h6">Sales Report Summary</Typography>
        {summary && (
          <Box display="flex" gap={3} mb={2}>
            <Chip label={`Total Sales: ${summary.total_sales}`} variant="outlined" />
            <Chip label={`Total Revenue: $${summary.total_revenue.toFixed(2)}`} variant="outlined" />
            <Chip label={`Period: ${summary.date_range}`} variant="outlined" />
          </Box>
        )}
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Receipt #</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Customer</TableCell>
              <TableCell>Warehouse</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Items</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {reportData.map((sale) => (
              <TableRow key={sale.id}>
                <TableCell>{sale.receipt_number}</TableCell>
                <TableCell>{new Date(sale.sale_date).toLocaleDateString()}</TableCell>
                <TableCell>{sale.customer_name}</TableCell>
                <TableCell>{sale.warehouse_name}</TableCell>
                <TableCell align="right">${sale.total_amount.toFixed(2)}</TableCell>
                <TableCell>
                  <Chip 
                    label={sale.payment_status} 
                    size="small" 
                    color={
                      sale.payment_status === 'completed' ? 'success' :
                      sale.payment_status === 'pending' ? 'warning' :
                      sale.payment_status === 'cancelled' ? 'error' : 'default'
                    }
                  />
                </TableCell>
                <TableCell>
                  {sale.items.map((item, idx) => (
                    <div key={idx}>
                      {item.quantity}x {item.product_name} (${item.unit_price.toFixed(2)})
                    </div>
                  ))}
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {reportData.length === 0 && (
        <Typography variant="body1" align="center" sx={{ mt: 2 }}>
          No sales found for the selected criteria.
        </Typography>
      )}
    </Box>
  );
};

export default SalesReport;