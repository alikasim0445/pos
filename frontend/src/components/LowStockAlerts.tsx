import React, { useEffect, useState } from 'react';
import { inventoryAPI } from '../services/api';
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
  Chip,
  Badge,
} from '@mui/material';

interface LowStockItem {
  id: number;
  product_name: string;
  product_sku: string;
  warehouse_name: string;
  available_stock: number;
  quantity_on_hand: number;
  min_stock_level: number;
  is_low_stock: boolean;
}

const LowStockAlerts: React.FC = () => {
  const [lowStockItems, setLowStockItems] = useState<LowStockItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    const fetchLowStockItems = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await inventoryAPI.getLowStockAlerts();
        setLowStockItems(response.data.low_stock_items);
      } catch (err: any) {
        setError(err.message || 'Failed to load low stock alerts');
        console.error('Error loading low stock alerts:', err);
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchLowStockItems();
    }
  }, [isAuthenticated]);

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
      <Box display="flex" alignItems="center" mb={3}>
        <Typography variant="h5" component="h2" sx={{ mr: 2 }}>
          Low Stock Alerts
        </Typography>
        <Badge badgeContent={lowStockItems.length} color="error">
          <Chip 
            label={`${lowStockItems.length} Items`} 
            color="error" 
            variant="outlined" 
          />
        </Badge>
      </Box>

      {lowStockItems.length === 0 ? (
        <Alert severity="success">No low stock items at this time.</Alert>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Product</TableCell>
                <TableCell>SKU</TableCell>
                <TableCell>Warehouse</TableCell>
                <TableCell align="right">Available Stock</TableCell>
                <TableCell align="right">On Hand</TableCell>
                <TableCell align="right">Min Level</TableCell>
                <TableCell align="center">Status</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {lowStockItems.map((item) => (
                <TableRow key={item.id}>
                  <TableCell component="th" scope="row">
                    {item.product_name}
                  </TableCell>
                  <TableCell>{item.product_sku}</TableCell>
                  <TableCell>{item.warehouse_name}</TableCell>
                  <TableCell align="right">
                    <Chip 
                      label={item.available_stock} 
                      color={item.available_stock <= 0 ? "error" : "warning"} 
                      size="small" 
                    />
                  </TableCell>
                  <TableCell align="right">{item.quantity_on_hand}</TableCell>
                  <TableCell align="right">{item.min_stock_level}</TableCell>
                  <TableCell align="center">
                    <Chip 
                      label="Low Stock" 
                      color="error" 
                      size="small" 
                    />
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}
    </Box>
  );
};

export default LowStockAlerts;