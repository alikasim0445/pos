import React, { useState, useEffect } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button, 
  TextField, 
  Box,
  CircularProgress
} from '@mui/material';
import { warehouseAPI } from '../services/api';

interface WarehouseFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (warehouse: any) => void;
  initialData?: any;
}

const WarehouseForm: React.FC<WarehouseFormProps> = ({ open, onClose, onSubmit, initialData }) => {
  const [formData, setFormData] = useState({
    name: '',
    location: '',
    contact_person: '',
    contact_phone: '',
    contact_email: '',
    capacity: ''
  });
  
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    if (open) {
      if (initialData) {
        setFormData({
          name: initialData.name || '',
          location: initialData.location || '',
          contact_person: initialData.contact_person || '',
          contact_phone: initialData.contact_phone || '',
          contact_email: initialData.contact_email || '',
          capacity: initialData.capacity?.toString() || ''
        });
      } else {
        resetForm();
      }
    }
  }, [open, initialData]);

  const resetForm = () => {
    setFormData({
      name: '',
      location: '',
      contact_person: '',
      contact_phone: '',
      contact_email: '',
      capacity: ''
    });
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleSubmit = async () => {
    setLoading(true);
    
    try {
      // Convert capacity to number
      const warehouseData = {
        ...formData,
        capacity: parseInt(formData.capacity) || 0
      };
      
      if (initialData && initialData.id) {
        // Update existing warehouse
        const response = await warehouseAPI.updateWarehouse(initialData.id, warehouseData);
        onSubmit(response.data);
      } else {
        // Create new warehouse
        const response = await warehouseAPI.createWarehouse(warehouseData);
        onSubmit(response.data);
      }
      
      onClose();
    } catch (error) {
      console.error('Failed to save warehouse:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {initialData ? 'Edit Warehouse' : 'Create New Warehouse'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <TextField
            autoFocus
            margin="dense"
            name="name"
            label="Warehouse Name"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={handleChange}
          />
          <TextField
            margin="dense"
            name="location"
            label="Location"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.location}
            onChange={handleChange}
          />
          <TextField
            margin="dense"
            name="contact_person"
            label="Contact Person"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.contact_person}
            onChange={handleChange}
          />
          <TextField
            margin="dense"
            name="contact_phone"
            label="Contact Phone"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.contact_phone}
            onChange={handleChange}
          />
          <TextField
            margin="dense"
            name="contact_email"
            label="Contact Email"
            type="email"
            fullWidth
            variant="outlined"
            value={formData.contact_email}
            onChange={handleChange}
          />
          <TextField
            margin="dense"
            name="capacity"
            label="Capacity"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.capacity}
            onChange={handleChange}
          />
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button onClick={handleSubmit} variant="contained" disabled={loading}>
          {loading ? <CircularProgress size={24} /> : (initialData ? 'Update' : 'Create')}
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default WarehouseForm;