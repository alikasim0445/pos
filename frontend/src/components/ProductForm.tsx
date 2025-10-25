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
  CircularProgress,
  InputAdornment,
  Typography,
  FormHelperText,
  Alert
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
    cost_price: '',
    wholesale_price: '',
    min_wholesale_qty: '1',
    tags: '',
    image: null as File | null
  });
  
  const [categories, setCategories] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingCategories, setLoadingCategories] = useState(true);
  const [errors, setErrors] = useState<{[key: string]: string}>({});

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
          cost_price: initialData.cost_price?.toString() || '',
          wholesale_price: initialData.wholesale_price?.toString() || '',
          min_wholesale_qty: initialData.min_wholesale_qty?.toString() || '1',
          tags: initialData.tags || '',
          image: null
        });
      } else {
        resetForm();
      }
      setErrors({});
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
      cost_price: '',
      wholesale_price: '',
      min_wholesale_qty: '1',
      tags: '',
      image: null
    });
    setErrors({});
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

  const validateForm = () => {
    const newErrors: {[key: string]: string} = {};
    
    if (!formData.name.trim()) {
      newErrors.name = 'Product name is required';
    }
    
    if (!formData.sku.trim()) {
      newErrors.sku = 'SKU is required';
    }
    
    if (!formData.price || parseFloat(formData.price) <= 0) {
      newErrors.price = 'Price must be greater than zero';
    }
    
    if (formData.cost_price && parseFloat(formData.cost_price) <= 0) {
      newErrors.cost_price = 'Cost price must be greater than zero';
    }
    
    if (formData.wholesale_price && parseFloat(formData.wholesale_price) <= 0) {
      newErrors.wholesale_price = 'Wholesale price must be greater than zero';
    }
    
    if (formData.min_wholesale_qty && parseInt(formData.min_wholesale_qty) <= 0) {
      newErrors.min_wholesale_qty = 'Minimum wholesale quantity must be greater than zero';
    }
    
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    // Clear error when user starts typing
    if (errors[name]) {
      setErrors(prev => ({ ...prev, [name]: '' }));
    }
  };

  const handleSelectChange = (e: any) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  const handleImageChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFormData(prev => ({
        ...prev,
        image: e.target.files![0]
      }));
    }
  };

  const handleSubmit = async () => {
    if (!validateForm()) {
      return;
    }
    
    setLoading(true);
    setErrors({});
    
    try {
      // Prepare form data for submission
      const productData = new FormData();
      productData.append('name', formData.name.trim());
      productData.append('sku', formData.sku.trim());
      productData.append('barcode', formData.barcode.trim());
      productData.append('description', formData.description.trim());
      
      if (formData.category) {
        productData.append('category', formData.category);
      }
      
      productData.append('price', (parseFloat(formData.price) || 0).toString());
      
      if (formData.cost_price) {
        productData.append('cost_price', (parseFloat(formData.cost_price)).toString());
      }
      
      if (formData.wholesale_price) {
        productData.append('wholesale_price', (parseFloat(formData.wholesale_price)).toString());
      }
      
      productData.append('min_wholesale_qty', (parseInt(formData.min_wholesale_qty) || 1).toString());
      productData.append('tags', formData.tags.trim());
      
      if (formData.image) {
        productData.append('image', formData.image);
      }
      
      let response;
      if (initialData && initialData.id) {
        // Update existing product
        response = await productAPI.updateProduct(initialData.id, productData);
      } else {
        // Create new product
        response = await productAPI.createProduct(productData);
      }
      
      console.log('API Response Data:', response.data); // Debug log
      onSubmit(response.data);
      onClose();
    } catch (error: any) {
      console.error('Failed to save product:', error);
      
      // Enhanced error handling
      if (error.response && error.response.data) {
        const errorData = error.response.data;
        if (typeof errorData === 'object') {
          // Set field-specific errors
          const fieldErrors: {[key: string]: string} = {};
          for (const [field, messages] of Object.entries(errorData)) {
            if (Array.isArray(messages)) {
              fieldErrors[field] = messages.join(', ');
            } else {
              fieldErrors[field] = messages as string;
            }
          }
          setErrors(fieldErrors);
        } else {
          setErrors({ general: errorData });
        }
      } else {
        setErrors({ general: 'An unexpected error occurred while saving the product' });
      }
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
          {errors.general && (
            <Alert severity="error">{errors.general}</Alert>
          )}
          
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
            error={!!errors.name}
            helperText={errors.name}
            required
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
            error={!!errors.sku}
            helperText={errors.sku}
            required
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
            error={!!errors.barcode}
            helperText={errors.barcode}
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
            error={!!errors.description}
            helperText={errors.description}
          />
          
          {loadingCategories ? (
            <CircularProgress />
          ) : (
            <FormControl fullWidth error={!!errors.category}>
              <InputLabel>Category</InputLabel>
              <Select
                name="category"
                value={formData.category}
                label="Category"
                onChange={handleSelectChange}
              >
                <MenuItem value="">
                  <em>No Category</em>
                </MenuItem>
                {categories.map((category: any) => (
                  <MenuItem key={category.id} value={category.id.toString()}>
                    {category.name}
                  </MenuItem>
                ))}
              </Select>
              {errors.category && <FormHelperText>{errors.category}</FormHelperText>}
            </FormControl>
          )}
          
          <TextField
            margin="dense"
            name="price"
            label="Retail Price"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.price}
            onChange={handleChange}
            InputProps={{
              startAdornment: <InputAdornment position="start">$</InputAdornment>,
              inputProps: { min: 0, step: 0.01 }
            }}
            error={!!errors.price}
            helperText={errors.price}
            required
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
            InputProps={{
              startAdornment: <InputAdornment position="start">$</InputAdornment>,
              inputProps: { min: 0, step: 0.01 }
            }}
            error={!!errors.cost_price}
            helperText={errors.cost_price}
          />
          
          <TextField
            margin="dense"
            name="wholesale_price"
            label="Wholesale Price"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.wholesale_price}
            onChange={handleChange}
            InputProps={{
              startAdornment: <InputAdornment position="start">$</InputAdornment>,
              inputProps: { min: 0, step: 0.01 }
            }}
            error={!!errors.wholesale_price}
            helperText={errors.wholesale_price}
          />
          
          <TextField
            margin="dense"
            name="min_wholesale_qty"
            label="Min. Quantity for Wholesale"
            type="number"
            fullWidth
            variant="outlined"
            value={formData.min_wholesale_qty}
            onChange={handleChange}
            InputProps={{ inputProps: { min: 1 } }}
            error={!!errors.min_wholesale_qty}
            helperText={errors.min_wholesale_qty}
          />
          
          <TextField
            margin="dense"
            name="tags"
            label="Tags (comma-separated)"
            type="text"
            fullWidth
            variant="outlined"
            value={formData.tags}
            onChange={handleChange}
            helperText="Separate tags with commas (e.g. organic, premium, seasonal)"
            error={!!errors.tags}
          />
          
          <input
            accept="image/*"
            style={{ display: 'none' }}
            id="product-image-upload"
            type="file"
            onChange={handleImageChange}
          />
          <label htmlFor="product-image-upload">
            <Button variant="outlined" component="span" fullWidth>
              Upload Product Image
            </Button>
          </label>
          {formData.image && (
            <Typography variant="body2" color="textSecondary">
              Selected: {formData.image.name}
            </Typography>
          )}
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