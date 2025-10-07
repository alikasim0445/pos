import React, { useState, useEffect } from 'react';
import { 
  Dialog, 
  DialogTitle, 
  DialogContent, 
  DialogActions, 
  Button, 
  TextField, 
  FormControl, 
  InputLabel, 
  Select, 
  MenuItem,
  Box,
  CircularProgress
} from '@mui/material';
import { productAPI, categoryAPI } from '../services/api';

interface ProductFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (product: any) => void;
  initialData?: any;
}

const ProductForm: React.FC<ProductFormProps> = ({ open, onClose, onSubmit, initialData }) => {
  const [formData, setFormData] = useState({
    name: '',
    sku: '',
    barcode: '',
    description: '',
    category: '',
    price: '',
    cost_price: ''
  });
  
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingCategories, setLoadingCategories] = useState(true);

  useEffect(() => {
    if (open) {
      loadCategories();
      if (initialData) {
        setFormData({
          name: initialData.name || '',
          sku: initialData.sku || '',
          barcode: initialData.barcode || '',
          description: initialData.description || '',
          category: initialData.category?.toString() || '',
          price: initialData.price?.toString() || '',
          cost_price: initialData.cost_price?.toString() || ''
        });
      } else {
        resetForm();
      }
    }
  }, [open, initialData]);

  const resetForm = () => {
    setFormData({
      name: '',
      sku: '',
      barcode: '',
      description: '',
      category: '',
      price: '',
      cost_price: ''
    });
  };

  const loadCategories = async () => {
    try {
      setLoadingCategories(true);
      const response = await categoryAPI.getCategories();
      setCategories(response.data);
    } catch (error) {
      console.error('Failed to load categories:', error);
    } finally {
      setLoadingCategories(false);
    }
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
      // Convert price and cost_price to numbers
      const productData = {
        ...formData,
        price: parseFloat(formData.price) || 0,
        cost_price: parseFloat(formData.cost_price) || null,
        category: parseInt(formData.category) || null
      };
      
      if (initialData && initialData.id) {
        // Update existing product
        const response = await productAPI.updateProduct(initialData.id, productData);
        onSubmit(response.data);
      } else {
        // Create new product
        const response = await productAPI.createProduct(productData);
        onSubmit(response.data);
      }
      
      onClose();
    } catch (error) {
      console.error('Failed to save product:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {initialData ? 'Edit Product' : 'Create New Product'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          <TextField
            autoFocus
            margin="dense"
            name="name"
            label="Product Name"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.name}
            onChange={handleChange}
          />
          <TextField
            margin="dense"
            name="sku"
            label="SKU"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.sku}
            onChange={handleChange}
          />
          <TextField
            margin="dense"
            name="barcode"
            label="Barcode"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.barcode}
            onChange={handleChange}
          />
          <TextField
            margin="dense"
            name="description"
            label="Description"
            type="text"
            fullWidth
            variant="outlined"
            multiline
            rows={3}
            value={formData.description}
            onChange={handleChange}
          />
          {loadingCategories ? (
            <CircularProgress />
          ) : (
            <FormControl fullWidth>
              <InputLabel>Category</InputLabel>
              <Select
                name="category"
                value={formData.category}
                label="Category"
                onChange={(e) => setFormData(prev => ({ ...prev, category: e.target.value }))}
              >
                {categories.map((category: any) => (
                  <MenuItem key={category.id} value={category.id.toString()}>
                    {category.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          )}
          <TextField
            margin="dense"
            name="price"
            label="Price"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.price}
            onChange={handleChange}
          />
          <TextField
            margin="dense"
            name="cost_price"
            label="Cost Price"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.cost_price}
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

export default ProductForm;