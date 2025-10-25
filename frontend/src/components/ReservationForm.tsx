import React, { useState, useEffect } from 'react';
import {
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  IconButton,
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Autocomplete,
  Box,
  Card,
  CardContent,
  Divider,
  Chip,
  Alert,
  InputAdornment,
} from '@mui/material';
import { 
  Add as AddIcon, 
  Delete as DeleteIcon, 
  Warehouse as WarehouseIcon,
  Inventory as InventoryIcon,
  Schedule as ScheduleIcon,
  Notes as NotesIcon
} from '@mui/icons-material';
import { Product, ProductVariant, Warehouse } from '../types';
import { productAPI, warehouseAPI } from '../services/api';

interface ReservationFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (data: any) => void;
  initialData?: any;
  isEditing?: boolean;
}

const ReservationForm: React.FC<ReservationFormProps> = ({ 
  open, 
  onClose, 
  onSubmit, 
  initialData, 
  isEditing 
}) => {
  const [formData, setFormData] = useState<any>({
    warehouse: null,
    notes: '',
    expires_at: '',
    lines: [],
  });
  const [products, setProducts] = useState<Product[]>([]);
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [selectedVariant, setSelectedVariant] = useState<ProductVariant | null>(null);
  const [quantity, setQuantity] = useState<number>(1);
  const [formError, setFormError] = useState<string | null>(null);

  useEffect(() => {
    if (open) {
      fetchProducts();
      fetchWarehouses();
      setFormError(null);
    }
  }, [open]);

  useEffect(() => {
    if (initialData && open) {
      // Format the data for editing
      setFormData({
        warehouse: initialData.warehouse,
        notes: initialData.notes || '',
        expires_at: initialData.expires_at ? new Date(initialData.expires_at).toISOString().slice(0, 16) : '',
        lines: initialData.lines || [],
      });
    } else {
      setFormData({
        warehouse: null,
        notes: '',
        expires_at: '',
        lines: [],
      });
    }
    setSelectedProduct(null);
    setSelectedVariant(null);
    setQuantity(1);
  }, [initialData, open]);

  const fetchProducts = async () => {
    try {
      const response = await productAPI.getProducts();
      setProducts(response.data);
    } catch (error) {
      console.error('Error fetching products:', error);
      setFormError('Failed to load products');
    }
  };

  const fetchWarehouses = async () => {
    try {
      const response = await warehouseAPI.getWarehouses();
      setWarehouses(response.data);
    } catch (error) {
      console.error('Error fetching warehouses:', error);
      setFormError('Failed to load warehouses');
    }
  };

  const validateForm = () => {
    if (!formData.warehouse) {
      setFormError('Please select a warehouse');
      return false;
    }
    if (!formData.expires_at) {
      setFormError('Please set an expiration date and time');
      return false;
    }
    if (formData.lines.length === 0) {
      setFormError('Please add at least one product to the reservation');
      return false;
    }
    
    // Validate expiration date is in the future
    const expiresAt = new Date(formData.expires_at);
    if (expiresAt <= new Date()) {
      setFormError('Expiration date must be in the future');
      return false;
    }
    
    setFormError(null);
    return true;
  };

  const handleAddProduct = () => {
    if (selectedProduct && quantity > 0) {
      // If product has variants, a variant must be selected
      if (selectedProduct.variants.length > 0 && !selectedVariant) {
        setFormError('Please select a product variant.');
        return;
      }

      const existingProductIndex = formData.lines.findIndex(
        (line: any) => line.product === selectedProduct.id && line.variant === (selectedVariant ? selectedVariant.id : null)
      );

      if (existingProductIndex >= 0) {
        // Update quantity if product already exists
        setFormData((prev: any) => {
          const newLines = [...prev.lines];
          newLines[existingProductIndex] = {
            ...newLines[existingProductIndex],
            quantity: newLines[existingProductIndex].quantity + quantity
          };
          return { ...prev, lines: newLines };
        });
      } else {
        // Add new product
        setFormData((prev: any) => ({
          ...prev,
          lines: [
            ...prev.lines, 
            { 
              product: selectedProduct.id,
              variant: selectedVariant ? selectedVariant.id : null,
              quantity: quantity,
              product_name: selectedProduct.name,
              variant_name: selectedVariant ? selectedVariant.name : null,
              product_sku: selectedVariant ? selectedVariant.sku : selectedProduct.sku
            }
          ],
        }));
      }
      setSelectedProduct(null);
      setSelectedVariant(null);
      setQuantity(1);
      setFormError(null);
    }
  };

  const handleRemoveProduct = (index: number) => {
    setFormData((prev: any) => ({
      ...prev,
      lines: prev.lines.filter((_: any, i: number) => i !== index),
    }));
  };

  const handleQuantityChange = (index: number, newQuantity: number) => {
    if (newQuantity > 0) {
      setFormData((prev: any) => {
        const newLines = [...prev.lines];
        newLines[index] = { 
          ...newLines[index], 
          quantity: newQuantity 
        };
        return { ...prev, lines: newLines };
      });
    }
  };

  const prepareSubmitData = () => {
    // Format the data for API submission
    const submitData = {
      warehouse: formData.warehouse?.id || formData.warehouse, // Send ID only
      notes: formData.notes,
      expires_at: formData.expires_at,
      lines: formData.lines.map((line: any) => ({
        product: line.product, // Just the product ID
        variant: line.variant, // Include variant ID
        quantity: line.quantity
      }))
    };
    return submitData;
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!validateForm()) return;
    
    const submitData = prepareSubmitData();
    onSubmit(submitData);
    onClose();
  };

  const getTotalItems = () => {
    return formData.lines.reduce((total: number, line: any) => total + line.quantity, 0);
  };

  const getProductDisplayName = (line: any) => {
    if (line.product_name) {
      return line.variant_name ? `${line.product_name} - ${line.variant_name}` : line.product_name;
    }
    const product = products.find(p => p.id === line.product);
    if (!product) return `Product ${line.product}`;

    if (line.variant) {
      const variant = product.variants.find(v => v.id === line.variant);
      return variant ? `${product.name} - ${variant.name}` : `${product.name} - Variant ${line.variant}`;
    }
    return product.name;
  };

  const getProductSku = (line: any) => {
    if (line.product_sku) {
      return line.product_sku;
    }
    const product = products.find(p => p.id === line.product);
    if (!product) return 'N/A';

    if (line.variant) {
      const variant = product.variants.find(v => v.id === line.variant);
      return variant ? variant.sku : 'N/A';
    }
    return product.sku;
  };

  return (
    <Dialog 
      open={open} 
      onClose={onClose} 
      maxWidth="lg" 
      fullWidth
      PaperProps={{ sx: { borderRadius: 2 } }}
    >
      <DialogTitle sx={{ 
        backgroundColor: 'primary.main', 
        color: 'white',
        py: 2
      }}>
        <Box display="flex" alignItems="center" gap={1}>
          <InventoryIcon />
          <Typography variant="h6" component="span" fontWeight="600">
            {isEditing ? 'Edit Reservation' : 'Create New Reservation'}
          </Typography>
        </Box>
      </DialogTitle>

      <form onSubmit={handleSubmit}>
        <DialogContent sx={{ p: 0 }}>
          {formError && (
            <Alert severity="error" sx={{ m: 3, mb: 2 }}>
              {formError}
            </Alert>
          )}

          <Box sx={{ p: 3 }}>
            <Grid container spacing={3}>
              {/* Basic Information Card */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined" sx={{ borderRadius: 2 }}>
                  <CardContent>
                    <Typography variant="h6" gutterBottom color="primary" fontWeight="600">
                      <WarehouseIcon sx={{ fontSize: 20, mr: 1 }} />
                      Reservation Details
                    </Typography>
                    <Divider sx={{ mb: 2 }} />

                    <Grid container spacing={2}>
                      <Grid item xs={12}>
                        <Autocomplete
                          options={warehouses}
                          isOptionEqualToValue={(option, value) => option.id === value.id}
                          getOptionLabel={(option) => `${option.name} - ${option.location}`}
                          value={formData.warehouse}
                          onChange={(e, newValue) => setFormData((prev: any) => ({ ...prev, warehouse: newValue }))}
                          renderInput={(params) => (
                            <TextField 
                              {...params} 
                              label="Warehouse" 
                              required
                              fullWidth
                              error={!formData.warehouse}
                              helperText={!formData.warehouse ? "Warehouse is required" : ""}
                            />
                          )}
                        />
                      </Grid>

                      <Grid item xs={12}>
                        <TextField
                          label="Expiration Date & Time"
                          type="datetime-local"
                          fullWidth
                          value={formData.expires_at}
                          onChange={(e) => setFormData((prev: any) => ({ ...prev, expires_at: e.target.value }))}
                          InputLabelProps={{ shrink: true }}
                          InputProps={{
                            startAdornment: (
                              <InputAdornment position="start">
                                <ScheduleIcon color="action" />
                              </InputAdornment>
                            ),
                          }}
                          error={!formData.expires_at}
                          helperText={!formData.expires_at ? "Expiration date is required" : ""}
                          required
                        />
                      </Grid>

                      <Grid item xs={12}>
                        <TextField
                          label="Notes"
                          fullWidth
                          multiline
                          rows={3}
                          value={formData.notes}
                          onChange={(e) => setFormData((prev: any) => ({ ...prev, notes: e.target.value }))}
                          placeholder="Add any additional notes about this reservation..."
                          InputProps={{
                            startAdornment: (
                              <InputAdornment position="start">
                                <NotesIcon color="action" />
                              </InputAdornment>
                            ),
                          }}
                        />
                      </Grid>
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>

              {/* Products Card */}
              <Grid item xs={12} md={6}>
                <Card variant="outlined" sx={{ borderRadius: 2 }}>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
                      <Typography variant="h6" color="primary" fontWeight="600">
                        <InventoryIcon sx={{ fontSize: 20, mr: 1 }} />
                        Products
                      </Typography>
                      {formData.lines.length > 0 && (
                        <Chip 
                          label={`${getTotalItems()} total items`} 
                          color="primary" 
                          variant="outlined" 
                          size="small" 
                        />
                      )}
                    </Box>
                    <Divider sx={{ mb: 2 }} />

                    {/* Add Product Section */}
                    <Paper variant="outlined" sx={{ p: 2, mb: 2, borderRadius: 2 }}>
                      <Typography variant="subtitle2" gutterBottom color="text.secondary">
                        Add Product
                      </Typography>
                      <Grid container spacing={1} alignItems="center">
                        <Grid item xs={12} sm={selectedProduct && selectedProduct.variants.length > 0 ? 6 : 9}>
                          <Autocomplete
                            options={products}
                            getOptionLabel={(option) => `${option.name} (SKU: ${option.sku})`}
                            value={selectedProduct}
                            onChange={(e, newValue) => {
                              setSelectedProduct(newValue);
                              setSelectedVariant(null); // Reset variant on product change
                            }}
                            renderInput={(params) => (
                              <TextField 
                                {...params} 
                                label="Select Product" 
                                size="small"
                              />
                            )}
                          />
                        </Grid>
                        {selectedProduct && selectedProduct.variants.length > 0 && (
                          <Grid item xs={12} sm={3}>
                            <Autocomplete
                              options={selectedProduct.variants}
                              getOptionLabel={(option) => option.name}
                              value={selectedVariant}
                              onChange={(e, newValue) => setSelectedVariant(newValue)}
                              renderInput={(params) => (
                                <TextField 
                                  {...params} 
                                  label="Select Variant" 
                                  size="small"
                                  error={!selectedVariant}
                                  helperText={!selectedVariant ? "Variant is required" : ""}
                                />
                              )}
                            />
                          </Grid>
                        )}
                        <Grid item xs={12} sm={3}>
                          <TextField
                            label="Qty"
                            type="number"
                            size="small"
                            fullWidth
                            value={quantity}
                            onChange={(e) => setQuantity(Math.max(1, parseInt(e.target.value) || 1))}
                            inputProps={{ min: 1 }}
                          />
                        </Grid>
                        <Grid item xs={12} sm={3}>
                          <Button 
                            variant="contained" 
                            onClick={handleAddProduct} 
                            startIcon={<AddIcon />}
                            disabled={!selectedProduct}
                            fullWidth
                            size="small"
                          >
                            Add
                          </Button>
                        </Grid>
                      </Grid>
                    </Paper>

                    {/* Products Table */}
                    {formData.lines.length > 0 ? (
                      <TableContainer component={Paper} variant="outlined">
                        <Table size="small">
                          <TableHead>
                            <TableRow sx={{ backgroundColor: 'grey.50' }}>
                              <TableCell sx={{ fontWeight: '600' }}>Product</TableCell>
                              <TableCell sx={{ fontWeight: '600', width: '100px' }}>Quantity</TableCell>
                              <TableCell sx={{ fontWeight: '600', width: '80px' }}>Actions</TableCell>
                            </TableRow>
                          </TableHead>
                          <TableBody>
                            {formData.lines.map((line: any, index: number) => (
                              <TableRow key={index} hover>
                                <TableCell>
                                  <Box>
                                    <Typography variant="body2" fontWeight="500">
                                      {getProductDisplayName(line)}
                                    </Typography>
                                    <Typography variant="caption" color="text.secondary">
                                      SKU: {getProductSku(line)}
                                    </Typography>
                                  </Box>
                                </TableCell>
                                <TableCell>
                                  <TextField
                                    type="number"
                                    size="small"
                                    value={line.quantity}
                                    onChange={(e) => handleQuantityChange(index, parseInt(e.target.value) || 1)}
                                    inputProps={{ 
                                      min: 1,
                                      style: { textAlign: 'center' }
                                    }}
                                    sx={{ width: '80px' }}
                                  />
                                </TableCell>
                                <TableCell>
                                  <IconButton 
                                    size="small" 
                                    onClick={() => handleRemoveProduct(index)}
                                    color="error"
                                  >
                                    <DeleteIcon fontSize="small" />
                                  </IconButton>
                                </TableCell>
                              </TableRow>
                            ))}
                          </TableBody>
                        </Table>
                      </TableContainer>
                    ) : (
                      <Paper 
                        variant="outlined" 
                        sx={{ 
                          p: 4, 
                          textAlign: 'center',
                          backgroundColor: 'grey.50',
                          borderRadius: 2
                        }}
                      >
                        <InventoryIcon color="disabled" sx={{ fontSize: 48, mb: 1 }} />
                        <Typography variant="body1" color="text.secondary">
                          No products added yet
                        </Typography>
                        <Typography variant="body2" color="text.secondary">
                          Use the form above to add products to your reservation
                        </Typography>
                      </Paper>
                    )}
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          </Box>
        </DialogContent>

        <DialogActions sx={{ p: 3, gap: 1 }}>
          <Button 
            onClick={onClose} 
            variant="outlined"
            size="large"
          >
            Cancel
          </Button>
          <Button 
            type="submit" 
            variant="contained" 
            size="large"
            disabled={formData.lines.length === 0}
          >
            {isEditing ? 'Update Reservation' : 'Create Reservation'}
          </Button>
        </DialogActions>
      </form>
    </Dialog>
  );
};

export default ReservationForm;