import React, { useEffect, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../hooks/redux';
import { productAPI, warehouseAPI, saleAPI, customerAPI } from '../services/api';
import LowStockAlerts from '../components/LowStockAlerts';
import {
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Alert,
} from '@mui/material';

const Dashboard: React.FC = () => {
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState({
    totalProducts: 0,
    totalWarehouses: 0,
    totalSales: 0,
    totalCustomers: 0,
  });

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        setLoading(true);
        setError(null);
        
        // Fetch products count
        const productsResponse = await productAPI.getProducts();
        const productsCount = productsResponse.data.length || 0;
        
        // Fetch warehouses count
        const warehousesResponse = await warehouseAPI.getWarehouses();
        const warehousesCount = warehousesResponse.data.length || 0;
        
        // Fetch sales count
        const salesResponse = await saleAPI.getSales();
        const salesCount = salesResponse.data.length || 0;
        
        // Fetch customers count
        const customersResponse = await customerAPI.getCustomers();
        const customersCount = customersResponse.data.length || 0;
        
        setStats({
          totalProducts: productsCount,
          totalWarehouses: warehousesCount,
          totalSales: salesCount,
          totalCustomers: customersCount,
        });
      } catch (err: any) {
        setError(err.message || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
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
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Dashboard</h1>
      <p className="text-gray-600 mb-8">Welcome, {user?.first_name || user?.email}! Here's an overview of your POS system.</p>
      
      <Grid container spacing={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Products
              </Typography>
              <Typography variant="h5" component="h2">
                {stats.totalProducts}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Warehouses
              </Typography>
              <Typography variant="h5" component="h2">
                {stats.totalWarehouses}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Sales
              </Typography>
              <Typography variant="h5" component="h2">
                {stats.totalSales}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Customers
              </Typography>
              <Typography variant="h5" component="h2">
                {stats.totalCustomers}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Additional dashboard components can be added here */}
      
      <Grid container spacing={3} sx={{ mt: 4 }}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <LowStockAlerts />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </div>
  );
};

export default Dashboard;