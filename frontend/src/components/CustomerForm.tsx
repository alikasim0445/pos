import React, { useState, useEffect } from 'react';
import {
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Button,
  TextField,
  Grid,
  Box,
  CircularProgress,
  Alert,
} from '@mui/material';
import { Customer } from '../types';

type CreateCustomerData = Omit<Customer, 'id' | 'created_at' | 'updated_at'>;
type UpdateCustomerData = Customer;

interface CustomerFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (customer: Customer | CreateCustomerData) => void;
  initialData?: Customer | null;
  loading?: boolean;
  error?: string | null;
}

type CustomerFormData = Omit<Customer, 'id' | 'created_at' | 'updated_at'> & { id?: number };

const CustomerForm: React.FC<CustomerFormProps> = ({
  open,
  onClose,
  onSubmit,
  initialData = null,
  loading = false,
  error = null,
}) => {
  const [formData, setFormData] = useState<CustomerFormData>({
    id: undefined,
    first_name: '',
    last_name: '',
    email: '',
    phone: '',
    loyalty_points: 0,
    is_active: true,
  });

  const [formErrors, setFormErrors] = useState<Record<string, string>>({});

  useEffect(() => {
    if (initialData) {
      setFormData({
        id: initialData.id,
        first_name: initialData.first_name,
        last_name: initialData.last_name,
        email: initialData.email || '',
        phone: initialData.phone || '',
        loyalty_points: initialData.loyalty_points,
        is_active: initialData.is_active,
      });
    } else {
      setFormData({
        id: undefined,
        first_name: '',
        last_name: '',
        email: '',
        phone: '',
        loyalty_points: 0,
        is_active: true,
      });
    }
  }, [initialData, open]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: name === 'loyalty_points' || name === 'id' ? Number(value) : value,
    }));
  };

  const validateForm = (): boolean => {
    const errors: Record<string, string> = {};
    if (!formData.first_name.trim()) {
      errors.first_name = 'First name is required';
    }
    if (!formData.last_name.trim()) {
      errors.last_name = 'Last name is required';
    }
    if (formData.email && !/^\S+@\S+\.\S+$/.test(formData.email)) {
      errors.email = 'Please enter a valid email';
    }
    if (formData.phone && !/^\d+$/.test(formData.phone.replace(/\D/g, ''))) {
      errors.phone = 'Please enter a valid phone number';
    }
    
    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    
    if (validateForm()) {
      // For creating new customers, don't include the id field
      if (initialData) {
        // This is an update, so we need the full customer object
        const updatedCustomer: Customer = {
          ...initialData,
          ...formData,
          id: initialData.id, // ensure the original ID is preserved for updates
        };
        onSubmit(updatedCustomer);
      } else {
        // This is a create, so we submit only the creation fields
        const createData: CreateCustomerData = {
          first_name: formData.first_name,
          last_name: formData.last_name,
          email: formData.email || '',
          phone: formData.phone || '',
          loyalty_points: formData.loyalty_points,
          is_active: formData.is_active,
        };
        onSubmit(createData);
      }
    }
  };

  const handleClose = () => {
    setFormErrors({});
    onClose();
  };

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <form onSubmit={handleSubmit}>
        <DialogTitle>
          {initialData ? 'Edit Customer' : 'Add New Customer'}
        </DialogTitle>
        <DialogContent dividers>
          <Box sx={{ pt: 1 }}>
            <Grid container spacing={2}>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="First Name"
                  name="first_name"
                  value={formData.first_name}
                  onChange={handleChange}
                  error={!!formErrors.first_name}
                  helperText={formErrors.first_name}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Last Name"
                  name="last_name"
                  value={formData.last_name}
                  onChange={handleChange}
                  error={!!formErrors.last_name}
                  helperText={formErrors.last_name}
                  required
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Email"
                  name="email"
                  type="email"
                  value={formData.email || ''}
                  onChange={handleChange}
                  error={!!formErrors.email}
                  helperText={formErrors.email}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Phone"
                  name="phone"
                  value={formData.phone || ''}
                  onChange={handleChange}
                  error={!!formErrors.phone}
                  helperText={formErrors.phone}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Loyalty Points"
                  name="loyalty_points"
                  type="number"
                  value={formData.loyalty_points}
                  onChange={handleChange}
                  inputProps={{ min: 0 }}
                />
              </Grid>
              <Grid item xs={12} sm={6}>
                <TextField
                  fullWidth
                  label="Status"
                  name="is_active"
                  value={formData.is_active ? 'Active' : 'Inactive'}
                  disabled
                  InputProps={{
                    readOnly: true,
                  }}
                />
              </Grid>
            </Grid>
            
            {error && (
              <Box sx={{ mt: 2 }}>
                <Alert severity="error">{error}</Alert>
              </Box>
            )}
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleClose} disabled={loading}>Cancel</Button>
          <Button 
            type="submit" 
            variant="contained" 
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : null}
          >
            {loading ? 'Saving...' : (initialData ? 'Update' : 'Create')}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default CustomerForm;