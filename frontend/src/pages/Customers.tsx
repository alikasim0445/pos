import React, { useEffect, useState } from 'react';
import { useAppSelector } from '../hooks/redux';
import { customerAPI } from '../services/api';
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
  TextField,
  MenuItem,
} from '@mui/material';
import { Add as AddIcon, History as HistoryIcon } from '@mui/icons-material';
import CustomerDetails from '../components/CustomerDetails';

interface Customer {
  id: number;
  first_name: string;
  last_name: string;
  email?: string;
  phone?: string;
  loyalty_points: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

const Customers: React.FC = () => {
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    const fetchCustomers = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await customerAPI.getCustomers();
        setCustomers(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load customers');
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchCustomers();
    }
  }, [isAuthenticated]);

  const handleCreateCustomer = () => {
    setEditingCustomer(null);
    setIsFormOpen(true);
  };

  const handleEditCustomer = (customer: Customer) => {
    setEditingCustomer(customer);
    setIsFormOpen(true);
  };

  const handleShowHistory = (id: number) => {
    setSelectedCustomerId(id);
    setShowHistory(true);
  };

  const handleFormSubmit = async (customer: Customer) => {
    if (editingCustomer) {
      // Update existing customer in the list
      setCustomers(prev => prev.map(c => c.id === customer.id ? customer : c));
    } else {
      // Add new customer to the list
      setCustomers(prev => [customer, ...prev]);
    }
    setIsFormOpen(false);
  };

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
      <h1 className="text-3xl font-bold text-gray-800 mb-6">Customers</h1>
      <Grid container spacing={3}>
        {customers.map((customer) => (
          <Grid item xs={12} sm={6} md={4} key={customer.id}>
            <Card>
              <CardContent>
                <Typography variant="h6" component="h2">
                  {customer.first_name} {customer.last_name}
                </Typography>
                {customer.email && (
                  <Typography color="textSecondary">Email: {customer.email}</Typography>
                )}
                {customer.phone && (
                  <Typography color="textSecondary">Phone: {customer.phone}</Typography>
                )}
                <Typography>Loyalty Points: {customer.loyalty_points}</Typography>
                <Box mt={2} display="flex" justifyContent="space-between">
                  <Button
                    variant="contained"
                    color="primary"
                    size="small"
                    onClick={() => handleShowHistory(customer.id)}
                    startIcon={<HistoryIcon />}
                  >
                    View History
                  </Button>
                  <Button
                    variant="outlined"
                    color="secondary"
                    size="small"
                    onClick={() => handleEditCustomer(customer)}
                  >
                    Edit
                  </Button>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
      
      {/* Add Customer Floating Action Button */}
      <Fab 
        color="primary" 
        aria-label="add" 
        style={{ position: 'fixed', bottom: 16, right: 16 }}
        onClick={handleCreateCustomer}
      >
        <AddIcon />
      </Fab>
      
      {/* Customer History Dialog */}
      <Dialog 
        open={showHistory} 
        onClose={() => setShowHistory(false)}
        maxWidth="lg"
        fullWidth
      >
        <DialogContent>
          {selectedCustomerId && (
            <CustomerDetails customerId={selectedCustomerId} />
          )}
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default Customers;