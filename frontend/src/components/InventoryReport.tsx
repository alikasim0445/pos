import React, { useState, useEffect } from 'react';
import { reportAPI } from '../services/api';
import { useAppSelector } from '../hooks/redux';
import { exportTableData } from '../utils/exportUtils';
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
  Button,
  Grid,
} from '@mui/material';
import { Download as DownloadIcon } from '@mui/icons-material';

interface InventoryReportItem {
  id: number;
  product_name: string;
  product_sku: string;
  category_name: string;
  warehouse_name: string;
  quantity_on_hand: number;
  quantity_reserved: number;
  available_stock: number;
  min_stock_level: number;
  is_low_stock: boolean;
  unit_price: number;
  total_value: number;
  last_updated: string;
}

interface InventoryReportProps {
  filters: {
    startDate: string;
    endDate: string;
    warehouseId: string;
    categoryId: string;
  };
  canExport: boolean;
}

const InventoryReport: React.FC<InventoryReportProps> = ({ filters, canExport }) => {
  const [reportData, setReportData] = useState<InventoryReportItem[]>([]);
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
        if (filters.warehouseId) params.warehouse_id = filters.warehouseId;
        if (filters.categoryId) params.category_id = filters.categoryId;
        
        const response = await reportAPI.getInventoryReport(params);
        setReportData(response.data.inventory);
        setSummary(response.data.summary);
      } catch (err: any) {
        setError(err.message || 'Failed to load inventory report');
        console.error('Error loading inventory report:', err);
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchReport();
    }
  }, [filters, isAuthenticated]);

  const handleExport = (format: 'csv' | 'excel' | 'pdf') => {
    if (!reportData || reportData.length === 0) {
      setError('No data to export');
      return;
    }

    // Prepare data for export
    const exportData = reportData.map(item => ({
      'Product': item.product_name,
      'SKU': item.product_sku,
      'Category': item.category_name,
      'Warehouse': item.warehouse_name,
      'On Hand': item.quantity_on_hand,
      'Reserved': item.quantity_reserved,
      'Available': item.available_stock,
      'Min Level': item.min_stock_level,
      'Unit Price': `${item.unit_price.toFixed(2)}`,
      'Total Value': `${item.total_value.toFixed(2)}`,
      'Status': item.is_low_stock ? 'Low Stock' : 'In Stock',
    }));

    const fileName = `inventory-report-${new Date().toISOString().split('T')[0]}.${format}`;
    exportTableData(exportData, format, fileName, 'Inventory Report');
  };

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
        <Grid container justifyContent="space-between" alignItems="center">
          <Grid item>
            <Typography variant="h6">Inventory Report Summary</Typography>
          </Grid>
          {canExport && (
            <Grid item>
              <Button 
                variant="outlined" 
                startIcon={<DownloadIcon />}
                onClick={() => handleExport('csv')}
                size="small"
                sx={{ mr: 1 }}
              >
                Export CSV
              </Button>
              <Button 
                variant="outlined" 
                startIcon={<DownloadIcon />}
                onClick={() => handleExport('excel')}
                size="small"
                sx={{ mr: 1 }}
              >
                Export Excel
              </Button>
              <Button 
                variant="outlined" 
                startIcon={<DownloadIcon />}
                onClick={() => handleExport('pdf')}
                size="small"
              >
                Export PDF
              </Button>
            </Grid>
          )}
        </Grid>
        {summary && (
          <Box display="flex" gap={3} mb={2}>
            <Chip label={`Total Items: ${summary.total_items}`} variant="outlined" />
            <Chip label={`Total Value: ${summary.total_value.toFixed(2)}`} variant="outlined" />
          </Box>
        )}
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Product</TableCell>
              <TableCell>SKU</TableCell>
              <TableCell>Category</TableCell>
              <TableCell>Warehouse</TableCell>
              <TableCell align="right">On Hand</TableCell>
              <TableCell align="right">Reserved</TableCell>
              <TableCell align="right">Available</TableCell>
              <TableCell align="right">Min Level</TableCell>
              <TableCell align="right">Unit Price</TableCell>
              <TableCell align="right">Total Value</TableCell>
              <TableCell>Status</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {reportData.map((item) => (
              <TableRow key={item.id}>
                <TableCell>{item.product_name}</TableCell>
                <TableCell>{item.product_sku}</TableCell>
                <TableCell>{item.category_name}</TableCell>
                <TableCell>{item.warehouse_name}</TableCell>
                <TableCell align="right">{item.quantity_on_hand}</TableCell>
                <TableCell align="right">{item.quantity_reserved}</TableCell>
                <TableCell align="right">
                  {item.available_stock}
                </TableCell>
                <TableCell align="right">{item.min_stock_level}</TableCell>
                <TableCell align="right">${item.unit_price.toFixed(2)}</TableCell>
                <TableCell align="right">${item.total_value.toFixed(2)}</TableCell>
                <TableCell>
                  <Chip 
                    label={item.is_low_stock ? "Low Stock" : "In Stock"} 
                    size="small" 
                    color={item.is_low_stock ? "error" : "success"} 
                  />
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {reportData.length === 0 && (
        <Typography variant="body1" align="center" sx={{ mt: 2 }}>
          No inventory found for the selected criteria.
        </Typography>
      )}
    </Box>
  );
};

export default InventoryReport;