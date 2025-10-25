import React, { useState, useEffect } from 'react';
import { useAppSelector } from '../hooks/redux';
import { reportAPI } from '../services/api';
import { exportTableData } from '../utils/exportUtils';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Grid,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';
import { Download as DownloadIcon } from '@mui/icons-material';

const AccountantDashboard: React.FC = () => {
  const [financialData, setFinancialData] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { user, isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    const fetchFinancialData = async () => {
      try {
        setLoading(true);
        setError(null);

        // Fetch all financial-related reports
        const [salesRes, profitabilityRes, inventoryRes] = await Promise.allSettled([
          reportAPI.getSalesReport({}),
          reportAPI.getProfitabilityReport({}),
          reportAPI.getInventoryReport({}),
        ]);

        const data = {
          sales: salesRes.status === 'fulfilled' ? salesRes.value.data : { summary: {}, sales: [] },
          profitability: profitabilityRes.status === 'fulfilled' ? profitabilityRes.value.data : { summary: {}, sales: [] },
          inventory: inventoryRes.status === 'fulfilled' ? inventoryRes.value.data : { summary: {}, inventory: [] },
        };

        setFinancialData(data);
      } catch (err: any) {
        setError(err.message || 'Failed to load financial data');
        console.error('Error loading financial data:', err);
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchFinancialData();
    }
  }, [isAuthenticated]);

  const handleExport = (reportType: string, format: 'csv' | 'excel' | 'pdf') => {
    if (!financialData) return;

    let exportData: any[] = [];
    let fileName: string = '';
    let reportTitle: string = '';

    switch(reportType) {
      case 'sales':
        exportData = financialData.sales.sales.map((sale: any) => ({
          'Receipt #': sale.receipt_number,
          'Date': new Date(sale.sale_date).toLocaleDateString(),
          'Customer': sale.customer_name,
          'Warehouse': sale.warehouse_name,
          'Amount': `$${sale.total_amount.toFixed(2)}`,
          'Status': sale.payment_status,
        }));
        fileName = `sales-summary-${new Date().toISOString().split('T')[0]}.${format}`;
        reportTitle = 'Sales Summary Report';
        break;
      case 'profitability':
        exportData = financialData.profitability.sales.map((sale: any) => ({
          'Receipt #': sale.receipt_number,
          'Date': new Date(sale.sale_date).toLocaleDateString(),
          'Revenue': `$${sale.total_revenue.toFixed(2)}`,
          'COGS': `$${sale.total_cogs.toFixed(2)}`,
          'Profit': `$${sale.profit.toFixed(2)}`,
          'Margin %': `${sale.profit_margin.toFixed(2)}%`,
        }));
        fileName = `profitability-summary-${new Date().toISOString().split('T')[0]}.${format}`;
        reportTitle = 'Profitability Summary Report';
        break;
      case 'inventory':
        exportData = financialData.inventory.inventory.map((item: any) => ({
          'Product': item.product_name,
          'SKU': item.product_sku,
          'Warehouse': item.warehouse_name,
          'Available': item.available_stock,
          'Unit Price': `$${item.unit_price.toFixed(2)}`,
          'Total Value': `$${item.total_value.toFixed(2)}`,
          'Status': item.is_low_stock ? 'Low Stock' : 'In Stock',
        }));
        fileName = `inventory-summary-${new Date().toISOString().split('T')[0]}.${format}`;
        reportTitle = 'Inventory Summary Report';
        break;
      default:
        return;
    }

    exportTableData(exportData, format, fileName, reportTitle);
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="500px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <div className="container mx-auto px-4 py-8">
      <Typography variant="h4" component="h1" gutterBottom className="text-gray-800">
        Accountant Dashboard
      </Typography>

      {financialData && (
        <>
          {/* Financial Summary Cards */}
          <Grid container spacing={3} mb={4}>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="textSecondary">Total Revenue</Typography>
                  <Typography variant="h4" color="primary.main">
                    ${financialData.profitability.summary?.total_revenue?.toFixed(2) || 0}
                  </Typography>
                  <Button 
                    variant="outlined" 
                    startIcon={<DownloadIcon />}
                    size="small"
                    onClick={() => handleExport('profitability', 'csv')}
                    sx={{ mt: 1 }}
                  >
                    Export
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="textSecondary">Total Profit</Typography>
                  <Typography variant="h4" color="success.main">
                    ${financialData.profitability.summary?.total_profit?.toFixed(2) || 0}
                  </Typography>
                  <Typography variant="body2">
                    Margin: {financialData.profitability.summary?.overall_profit_margin?.toFixed(2) || 0}%
                  </Typography>
                  <Button 
                    variant="outlined" 
                    startIcon={<DownloadIcon />}
                    size="small"
                    onClick={() => handleExport('profitability', 'csv')}
                    sx={{ mt: 1 }}
                  >
                    Export
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            <Grid item xs={12} md={4}>
              <Card>
                <CardContent>
                  <Typography variant="h6" color="textSecondary">Total Sales</Typography>
                  <Typography variant="h4" color="textPrimary">
                    {financialData.sales.summary?.total_sales || 0}
                  </Typography>
                  <Typography variant="body2">
                    Period: {financialData.sales.summary?.date_range || 'N/A'}
                  </Typography>
                  <Button 
                    variant="outlined" 
                    startIcon={<DownloadIcon />}
                    size="small"
                    onClick={() => handleExport('sales', 'csv')}
                    sx={{ mt: 1 }}
                  >
                    Export
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>

          {/* Recent Transactions */}
          <Grid container spacing={3}>
            <Grid item xs={12} lg={8}>
              <Paper sx={{ p: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">Recent Sales</Typography>
                  <Button 
                    variant="outlined" 
                    startIcon={<DownloadIcon />}
                    size="small"
                    onClick={() => handleExport('sales', 'csv')}
                  >
                    Export All
                  </Button>
                </Box>
                <TableContainer>
                  <Table>
                    <TableHead>
                      <TableRow>
                        <TableCell>Receipt #</TableCell>
                        <TableCell>Date</TableCell>
                        <TableCell>Customer</TableCell>
                        <TableCell align="right">Amount</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {financialData.sales.sales.slice(0, 5).map((sale: any) => (
                        <TableRow key={sale.id}>
                          <TableCell>{sale.receipt_number}</TableCell>
                          <TableCell>{new Date(sale.sale_date).toLocaleDateString()}</TableCell>
                          <TableCell>{sale.customer_name}</TableCell>
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
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Grid>

            <Grid item xs={12} lg={4}>
              <Paper sx={{ p: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                  <Typography variant="h6">Low Stock Items</Typography>
                  <Button 
                    variant="outlined" 
                    startIcon={<DownloadIcon />}
                    size="small"
                    onClick={() => handleExport('inventory', 'csv')}
                  >
                    Export All
                  </Button>
                </Box>
                <TableContainer>
                  <Table size="small">
                    <TableHead>
                      <TableRow>
                        <TableCell>Product</TableCell>
                        <TableCell align="right">Available</TableCell>
                        <TableCell>Status</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {financialData.inventory.inventory
                        .filter((item: any) => item.is_low_stock)
                        .slice(0, 5)
                        .map((item: any) => (
                          <TableRow key={item.id}>
                            <TableCell>{item.product_name}</TableCell>
                            <TableCell align="right">{item.available_stock}</TableCell>
                            <TableCell>
                              <Chip 
                                label="Low Stock" 
                                size="small" 
                                color="error" 
                              />
                            </TableCell>
                          </TableRow>
                        ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </Paper>
            </Grid>
          </Grid>
        </>
      )}
    </div>
  );
};

export default AccountantDashboard;