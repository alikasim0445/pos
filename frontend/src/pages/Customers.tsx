import React, { useEffect, useState } from 'react';
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import { customerAPI } from '../services/api';
import { Customer } from '../types';
import CustomerForm from '../components/CustomerForm';
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
  DialogActions,
  DialogContentText,
} from '@mui/material';
import { Add as AddIcon, History as HistoryIcon, Delete as DeleteIcon } from '@mui/icons-material';
import CustomerDetails from '../components/CustomerDetails';

const Customers: React.FC = () => {
  const dispatch = useAppDispatch();
  const [customers, setCustomers] = useState<Customer[]>([]);
  const [loading, setLoading] = useState(true);
  const [formLoading, setFormLoading] = useState(false);
  const [deleteLoading, setDeleteLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingCustomer, setEditingCustomer] = useState<Customer | null>(null);
  const [showHistory, setShowHistory] = useState(false);
  const [selectedCustomerId, setSelectedCustomerId] = useState<number | null>(null);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [customerToDelete, setCustomerToDelete] = useState<Customer | null>(null);
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
    setFormError(null);
    setIsFormOpen(true);
  };

  const handleEditCustomer = (customer: Customer) => {
    setEditingCustomer(customer);
    setFormError(null);
    setIsFormOpen(true);
  };

  const handleShowHistory = (id: number) => {
    setSelectedCustomerId(id);
    setShowHistory(true);
  };

  const handleFormSubmit = async (customerData: Customer | Omit<Customer, 'id' | 'created_at' | 'updated_at'>) => {
    setFormLoading(true);
    setFormError(null);
    
    try {
      if (editingCustomer && 'id' in customerData && customerData.id) {
        // Update existing customer
        const response = await customerAPI.updateCustomer(customerData.id, customerData);
        setCustomers(prev => prev.map(c => c.id === customerData.id ? response.data : c));
      } else {
        // Create new customer - ensure no id field is sent
        const createPayload = {
          first_name: customerData.first_name,
          last_name: customerData.last_name,
          email: customerData.email || '',
          phone: customerData.phone || '',
          loyalty_points: customerData.loyalty_points,
          is_active: customerData.is_active,
        };
        
        const response = await customerAPI.createCustomer(createPayload);
        setCustomers(prev => [response.data, ...prev]);
      }
      setIsFormOpen(false);
      setFormError(null);
    } catch (err: any) {
      setFormError(err.message || 'Failed to save customer');
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteDialogOpen = (customer: Customer) => {
    setCustomerToDelete(customer);
    setDeleteDialogOpen(true);
  };

  const handleDeleteDialogClose = () => {
    setDeleteDialogOpen(false);
    setCustomerToDelete(null);
  };

  const handleDeleteCustomer = async () => {
    if (!customerToDelete) return;
    
    setDeleteLoading(true);
    try {
      await customerAPI.deleteCustomer(customerToDelete.id);
      setCustomers(prev => prev.filter(c => c.id !== customerToDelete.id));
      handleDeleteDialogClose();
    } catch (err: any) {
      setError(err.message || 'Failed to delete customer');
    } finally {
      setDeleteLoading(false);
    }
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
                  <Box>
                    <Button
                      variant="outlined"
                      color="secondary"
                      size="small"
                      onClick={() => handleEditCustomer(customer)}
                    >
                      Edit
                    </Button>
                    <Button
                      variant="outlined"
                      color="error"
                      size="small"
                      onClick={() => handleDeleteDialogOpen(customer)}
                      sx={{ ml: 1 }}
                    >
                      Delete
                    </Button>
                  </Box>
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
        style={{ position: 'fixed', bottom: 80, right: 16 }}
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
      
      {/* Customer Form Dialog */}
      <CustomerForm
        open={isFormOpen}
        onClose={() => {
          setIsFormOpen(false);
          setFormError(null);
        }}
        onSubmit={handleFormSubmit}
        initialData={editingCustomer}
        loading={formLoading}
        error={formError}
      />
      
      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteDialogClose}
        aria-labelledby="delete-customer-dialog-title"
        aria-describedby="delete-customer-dialog-description"
      >
        <DialogContent>
          <DialogContentText id="delete-customer-dialog-description">
            Are you sure you want to delete customer <strong>{customerToDelete?.first_name} {customerToDelete?.last_name}</strong>? 
            This action cannot be undone.
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteDialogClose} disabled={deleteLoading}>Cancel</Button>
          <Button 
            onClick={handleDeleteCustomer} 
            color="error" 
            disabled={deleteLoading}
            variant="contained"
          >
            {deleteLoading ? 'Deleting...' : 'Delete'}
          </Button>
        </DialogActions>
      </Dialog>
    </div>
  );
};

export default Customers;