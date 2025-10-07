import React, { useState } from 'react';
import {
  Box,
  Typography,
  Card,
  CardContent,
  Tabs,
  Tab,
  TextField,
  Button,
  Grid,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
} from '@mui/material';
import SalesReport from '../components/SalesReport';
import InventoryReport from '../components/InventoryReport';
import ProfitabilityReport from '../components/ProfitabilityReport';
import TransferReport from '../components/TransferReport';

const Reports: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [filters, setFilters] = useState({
    startDate: '',
    endDate: '',
    warehouseId: '',
    categoryId: '',
  });

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  const handleFilterChange = (field: string, value: string) => {
    setFilters(prev => ({
      ...prev,
      [field]: value
    }));
  };

  const applyFilters = () => {
    console.log('Applying filters:', filters);
  };

  return (
    <div className="container mx-auto px-4 py-8">
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Reports</h1>
      
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Grid container spacing={2} alignItems="center">
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="Start Date"
                type="date"
                value={filters.startDate}
                onChange={(e) => handleFilterChange('startDate', e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <TextField
                fullWidth
                label="End Date"
                type="date"
                value={filters.endDate}
                onChange={(e) => handleFilterChange('endDate', e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Warehouse</InputLabel>
                <Select
                  value={filters.warehouseId}
                  onChange={(e) => handleFilterChange('warehouseId', e.target.value)}
                >
                  <MenuItem value="">All Warehouses</MenuItem>
                  <MenuItem value="1">Main Warehouse</MenuItem>
                  <MenuItem value="2">Secondary Warehouse</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select
                  value={filters.categoryId}
                  onChange={(e) => handleFilterChange('categoryId', e.target.value)}
                >
                  <MenuItem value="">All Categories</MenuItem>
                  <MenuItem value="1">Electronics</MenuItem>
                  <MenuItem value="2">Clothing</MenuItem>
                  <MenuItem value="3">Home & Garden</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12} md={2}>
              <Button 
                variant="contained" 
                onClick={applyFilters}
                sx={{ height: '100%', width: '100%' }}
              >
                Apply Filters
              </Button>
            </Grid>
          </Grid>
        </CardContent>
      </Card>
      
      <Tabs value={activeTab} onChange={handleTabChange} sx={{ mb: 3 }}>
        <Tab label="Sales Report" />
        <Tab label="Inventory Report" />
        <Tab label="Profitability Report" />
        <Tab label="Transfer Report" />
      </Tabs>
      
      <Box>
        {activeTab === 0 && <SalesReport filters={filters} />}
        {activeTab === 1 && <InventoryReport filters={filters} />}
        {activeTab === 2 && <ProfitabilityReport filters={filters} />}
        {activeTab === 3 && <TransferReport filters={filters} />}
      </Box>
    </div>
  );
};

export default Reports;