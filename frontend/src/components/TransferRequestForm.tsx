import React, { useState, useEffect } from 'react';
import { useAppSelector } from '../hooks/redux';
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
  Alert,
  Typography,
  IconButton,
  Card,
  CardContent,
  Grid,
  Divider,
  Paper,
} from '@mui/material';
import { Add as AddIcon, Delete as DeleteIcon, LocationOn, Warehouse as WarehouseIcon } from '@mui/icons-material';
import { transferAPI, warehouseAPI, productAPI, locationAPI, binAPI } from '../services/api';
import { Transfer, Warehouse, Product } from '../types';

interface TransferRequestFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (transfer: Transfer) => void;
}

const TransferRequestForm: React.FC<TransferRequestFormProps> = ({ open, onClose, onSubmit }) => {
  const [formData, setFormData] = useState({
    from_warehouse: '',
    from_location: '',
    from_bin: '',
    to_warehouse: '',
    to_location: '',
    to_bin: '',
    notes: '',
    lines: [
      {
        product: '',
        requested_qty: '1'
      }
    ] as Array<{ product: string; requested_qty: string }>
  });
  
  const [warehouses, setWarehouses] = useState<Warehouse[]>([]);
  const [products, setProducts] = useState<Product[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingWarehouses, setLoadingWarehouses] = useState(true);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [loadingFromLocations, setLoadingFromLocations] = useState(false);
  const [loadingToLocations, setLoadingToLocations] = useState(false);
  const [loadingFromBins, setLoadingFromBins] = useState(false);
  const [loadingToBins, setLoadingToBins] = useState(false);
  const [fromLocations, setFromLocations] = useState<any[]>([]);
  const [toLocations, setToLocations] = useState<any[]>([]);
  const [fromBins, setFromBins] = useState<any[]>([]);
  const [toBins, setToBins] = useState<any[]>([]);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    if (open) {
      loadWarehouses();
      loadProducts();
    }
  }, [open]);

  const loadWarehouses = async () => {
    try {
      setLoadingWarehouses(true);
      const response = await warehouseAPI.getWarehouses();
      setWarehouses(response.data);
    } catch (error) {
      console.error('Failed to load warehouses:', error);
      setFormError('Failed to load warehouses');
    } finally {
      setLoadingWarehouses(false);
    }
  };

  const loadProducts = async () => {
    try {
      setLoadingProducts(true);
      const response = await productAPI.getProducts();
      setProducts(response.data);
    } catch (error) {
      console.error('Failed to load products:', error);
      setFormError('Failed to load products');
    } finally {
      setLoadingProducts(false);
    }
  };

  const loadFromLocations = async (warehouseId: string) => {
    if (!warehouseId) {
      setFromLocations([]);
      return;
    }
    
    try {
      setLoadingFromLocations(true);
      const response = await locationAPI.getLocationsByWarehouse(warehouseId);
      setFromLocations(response.data);
    } catch (error) {
      console.error('Failed to load source locations:', error);
      setFromLocations([]);
    } finally {
      setLoadingFromLocations(false);
    }
  };

  const loadToLocations = async (warehouseId: string) => {
    if (!warehouseId) {
      setToLocations([]);
      return;
    }
    
    try {
      setLoadingToLocations(true);
      const response = await locationAPI.getLocationsByWarehouse(warehouseId);
      setToLocations(response.data);
    } catch (error) {
      console.error('Failed to load destination locations:', error);
      setToLocations([]);
    } finally {
      setLoadingToLocations(false);
    }
  };

  const loadFromBins = async (locationId: string) => {
    if (!locationId) {
      setFromBins([]);
      return;
    }
    
    try {
      setLoadingFromBins(true);
      const response = await binAPI.getBinsByLocation(locationId);
      setFromBins(response.data);
    } catch (error) {
      console.error('Failed to load source bins:', error);
      setFromBins([]);
    } finally {
      setLoadingFromBins(false);
    }
  };

  const loadToBins = async (locationId: string) => {
    if (!locationId) {
      setToBins([]);
      return;
    }
    
    try {
      setLoadingToBins(true);
      const response = await binAPI.getBinsByLocation(locationId);
      setToBins(response.data);
    } catch (error) {
      console.error('Failed to load destination bins:', error);
      setToBins([]);
    } finally {
      setLoadingToBins(false);
    }
  };

  const handleSelectChange = (name: string, value: string) => {
    setFormData(prev => {
      const newState = { ...prev, [name]: value };
      
      // Reset dependent fields when parent changes
      if (name === 'from_warehouse') {
        newState.from_location = '';
        newState.from_bin = '';
        setFromLocations([]);
        setFromBins([]);
        if (value) {
          loadFromLocations(value);
        }
        
        // If same warehouse is selected for both, reset to locations and bins
        if (value === prev.to_warehouse) {
          newState.to_location = '';
          newState.to_bin = '';
          setToLocations([]);
          setToBins([]);
          loadToLocations(value);
        }
      } else if (name === 'from_location') {
        newState.from_bin = '';
        setFromBins([]);
        if (value) {
          loadFromBins(value);
        }
        
        // If same location is selected for both, reset to bin
        if (value === prev.to_location && prev.from_warehouse === prev.to_warehouse) {
          newState.to_bin = '';
          setToBins([]);
          loadToBins(value);
        }
      } else if (name === 'to_warehouse') {
        newState.to_location = '';
        newState.to_bin = '';
        setToLocations([]);
        setToBins([]);
        if (value) {
          loadToLocations(value);
        }
        
        // If same warehouse is selected for both, reset from locations and bins
        if (value === prev.from_warehouse) {
          newState.from_location = '';
          newState.from_bin = '';
          setFromLocations([]);
          setFromBins([]);
          loadFromLocations(value);
        }
      } else if (name === 'to_location') {
        newState.to_bin = '';
        setToBins([]);
        if (value) {
          loadToBins(value);
        }
        
        // If same location is selected for both, reset from bin
        if (value === prev.from_location && prev.from_warehouse === prev.to_warehouse) {
          newState.from_bin = '';
          setFromBins([]);
          loadFromBins(value);
        }
      }
      
      return newState;
    });
  };

  const handleLineChange = (index: number, field: string, value: string) => {
    setFormData(prev => {
      const newLines = [...prev.lines];
      newLines[index] = { ...newLines[index], [field]: value };
      return { ...prev, lines: newLines };
    });
  };

  const addLine = () => {
    setFormData(prev => ({
      ...prev,
      lines: [...prev.lines, { product: '', requested_qty: '1' }]
    }));
  };

  const removeLine = (index: number) => {
    if (formData.lines.length > 1) {
      setFormData(prev => ({
        ...prev,
        lines: prev.lines.filter((_, i) => i !== index)
      }));
    }
  };

  const validateForm = () => {
    if (!formData.from_warehouse) {
      setFormError('Please select a source warehouse');
      return false;
    }
    
    if (!formData.to_warehouse) {
      setFormError('Please select a destination warehouse');
      return false;
    }

    // Check if source and destination are exactly the same
    const isSameWarehouse = formData.from_warehouse === formData.to_warehouse;
    const isSameLocation = formData.from_location === formData.to_location;
    const isSameBin = formData.from_bin === formData.to_bin;

    if (isSameWarehouse && isSameLocation && isSameBin) {
      setFormError('Source and destination cannot be exactly the same. Please select different locations or bins within the same warehouse.');
      return false;
    }

    for (const line of formData.lines) {
      if (!line.product || !line.requested_qty || parseInt(line.requested_qty) <= 0) {
        setFormError('Please fill in all product and quantity fields');
        return false;
      }
    }

    setFormError(null);
    return true;
  };

  const { user } = useAppSelector((state) => state.auth);

  const handleSubmit = async (status: 'draft' | 'requested' = 'requested') => {
    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    setFormError(null);

    try {
      // Prepare transfer data
      const transferData = {
        from_warehouse: parseInt(formData.from_warehouse),
        from_location: formData.from_location ? parseInt(formData.from_location) : null,
        from_bin: formData.from_bin ? parseInt(formData.from_bin) : null,
        to_warehouse: parseInt(formData.to_warehouse),
        to_location: formData.to_location ? parseInt(formData.to_location) : null,
        to_bin: formData.to_bin ? parseInt(formData.to_bin) : null,
        notes: formData.notes,
        status: status,
        requested_by: user?.id,
        lines: formData.lines.map(line => ({
          product: parseInt(line.product),
          requested_qty: parseInt(line.requested_qty)
        }))
      };

      const response = await transferAPI.createTransfer(transferData);
      onSubmit(response.data);
      
      // Reset form and close dialog
      setFormData({
        from_warehouse: '',
        from_location: '',
        from_bin: '',
        to_warehouse: '',
        to_location: '',
        to_bin: '',
        notes: '',
        lines: [{ product: '', requested_qty: '1' }]
      });
      onClose();
    } catch (error: any) {
      console.error('Failed to create transfer:', error);
      if (error.response && error.response.data) {
        const errorData = error.response.data;
        let errorMessage = 'Validation errors occurred:\n';
        for (const [field, messages] of Object.entries(errorData)) {
          if (Array.isArray(messages)) {
            errorMessage += `${field}: ${messages.join(', ')}\n`;
          } else {
            errorMessage += `${field}: ${messages}\n`;
          }
        }
        setFormError(errorMessage);
      } else {
        setFormError(error.message || 'Failed to create transfer');
      }
    } finally {
      setSubmitting(false);
    }
  };

  if (loading && (loadingWarehouses || loadingProducts)) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <WarehouseIcon color="primary" />
            Create Transfer Request
          </Box>
        </DialogTitle>
        <DialogContent>
          <Box display="flex" justifyContent="center" alignItems="center" minHeight="200px">
            <CircularProgress />
          </Box>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="lg" fullWidth PaperProps={{ sx: { borderRadius: 2 } }}>
      <DialogTitle sx={{ 
        backgroundColor: 'primary.main', 
        color: 'white',
        py: 2
      }}>
        <Box display="flex" alignItems="center" gap={1}>
          <WarehouseIcon />
          <Typography variant="h6" component="span" fontWeight="600">
            {formData.from_warehouse ? 'Edit Transfer Request' : 'Create Transfer Request'}
          </Typography>
        </Box>
      </DialogTitle>
      
      <DialogContent sx={{ p: 0 }}>
        {formError && (
          <Alert severity="error" sx={{ m: 3, mb: 0 }}>
            {formError}
          </Alert>
        )}
        
        <Box sx={{ p: 3 }}>
          {/* Source and Destination Section */}
          <Paper elevation={1} sx={{ p: 3, mb: 3, borderRadius: 2 }}>
            <Typography variant="h6" gutterBottom color="primary" fontWeight="600">
              Transfer Details
            </Typography>
            <Divider sx={{ mb: 3 }} />
            
            <Grid container spacing={3}>
              {/* Source Column */}
              <Grid item xs={12} md={6}>
                <Box sx={{ p: 2, backgroundColor: 'grey.50', borderRadius: 2 }}>
                  <Typography variant="subtitle1" gutterBottom fontWeight="600" color="primary">
                    <LocationOn sx={{ fontSize: 18, mr: 1 }} />
                    Source
                  </Typography>
                  
                  <FormControl fullWidth required sx={{ mb: 2 }}>
                    <InputLabel>Warehouse</InputLabel>
                    <Select
                      value={formData.from_warehouse}
                      label="Warehouse"
                      onChange={(e) => handleSelectChange('from_warehouse', e.target.value)}
                    >
                      {warehouses.map(warehouse => (
                        <MenuItem key={warehouse.id} value={warehouse.id.toString()}>
                          <Box>
                            <Typography variant="body1" fontWeight="500">
                              {warehouse.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {warehouse.location}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Location</InputLabel>
                    <Select
                      value={formData.from_location}
                      label="Location"
                      onChange={(e) => handleSelectChange('from_location', e.target.value)}
                      disabled={loadingFromLocations || !formData.from_warehouse}
                    >
                      {loadingFromLocations ? (
                        <MenuItem disabled>
                          <Box display="flex" alignItems="center" gap={1}>
                            <CircularProgress size={16} />
                            Loading locations...
                          </Box>
                        </MenuItem>
                      ) : (
                        <>
                          <MenuItem value="">None (Optional)</MenuItem>
                          {fromLocations.map(location => (
                            <MenuItem key={location.id} value={location.id.toString()}>
                              <Box>
                                <Typography variant="body2" fontWeight="500">
                                  {location.name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {location.code}
                                </Typography>
                              </Box>
                            </MenuItem>
                          ))}
                        </>
                      )}
                    </Select>
                  </FormControl>
                  
                  <FormControl fullWidth>
                    <InputLabel>Bin</InputLabel>
                    <Select
                      value={formData.from_bin}
                      label="Bin"
                      onChange={(e) => handleSelectChange('from_bin', e.target.value)}
                      disabled={loadingFromBins || !formData.from_location}
                    >
                      {loadingFromBins ? (
                        <MenuItem disabled>
                          <Box display="flex" alignItems="center" gap={1}>
                            <CircularProgress size={16} />
                            Loading bins...
                          </Box>
                        </MenuItem>
                      ) : (
                        <>
                          <MenuItem value="">None (Optional)</MenuItem>
                          {fromBins.map(bin => (
                            <MenuItem key={bin.id} value={bin.id.toString()}>
                              <Box>
                                <Typography variant="body2" fontWeight="500">
                                  {bin.name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {bin.code}
                                </Typography>
                              </Box>
                            </MenuItem>
                          ))}
                        </>
                      )}
                    </Select>
                  </FormControl>
                </Box>
              </Grid>
              
              {/* Destination Column */}
              <Grid item xs={12} md={6}>
                <Box sx={{ p: 2, backgroundColor: 'success.light', borderRadius: 2 }}>
                  <Typography variant="subtitle1" gutterBottom fontWeight="600" color="success.dark">
                    <LocationOn sx={{ fontSize: 18, mr: 1 }} />
                    Destination
                  </Typography>
                  
                  <FormControl fullWidth required sx={{ mb: 2 }}>
                    <InputLabel>Warehouse</InputLabel>
                    <Select
                      value={formData.to_warehouse}
                      label="Warehouse"
                      onChange={(e) => handleSelectChange('to_warehouse', e.target.value)}
                    >
                      {warehouses.map(warehouse => (
                        <MenuItem key={warehouse.id} value={warehouse.id.toString()}>
                          <Box>
                            <Typography variant="body1" fontWeight="500">
                              {warehouse.name}
                            </Typography>
                            <Typography variant="caption" color="text.secondary">
                              {warehouse.location}
                            </Typography>
                          </Box>
                        </MenuItem>
                      ))}
                    </Select>
                  </FormControl>
                  
                  <FormControl fullWidth sx={{ mb: 2 }}>
                    <InputLabel>Location</InputLabel>
                    <Select
                      value={formData.to_location}
                      label="Location"
                      onChange={(e) => handleSelectChange('to_location', e.target.value)}
                      disabled={loadingToLocations || !formData.to_warehouse}
                    >
                      {loadingToLocations ? (
                        <MenuItem disabled>
                          <Box display="flex" alignItems="center" gap={1}>
                            <CircularProgress size={16} />
                            Loading locations...
                          </Box>
                        </MenuItem>
                      ) : (
                        <>
                          <MenuItem value="">None (Optional)</MenuItem>
                          {toLocations.map(location => (
                            <MenuItem key={location.id} value={location.id.toString()}>
                              <Box>
                                <Typography variant="body2" fontWeight="500">
                                  {location.name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {location.code}
                                </Typography>
                              </Box>
                            </MenuItem>
                          ))}
                        </>
                      )}
                    </Select>
                  </FormControl>
                  
                  <FormControl fullWidth>
                    <InputLabel>Bin</InputLabel>
                    <Select
                      value={formData.to_bin}
                      label="Bin"
                      onChange={(e) => handleSelectChange('to_bin', e.target.value)}
                      disabled={loadingToBins || !formData.to_location}
                    >
                      {loadingToBins ? (
                        <MenuItem disabled>
                          <Box display="flex" alignItems="center" gap={1}>
                            <CircularProgress size={16} />
                            Loading bins...
                          </Box>
                        </MenuItem>
                      ) : (
                        <>
                          <MenuItem value="">None (Optional)</MenuItem>
                          {toBins.map(bin => (
                            <MenuItem key={bin.id} value={bin.id.toString()}>
                              <Box>
                                <Typography variant="body2" fontWeight="500">
                                  {bin.name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  {bin.code}
                                </Typography>
                              </Box>
                            </MenuItem>
                          ))}
                        </>
                      )}
                    </Select>
                  </FormControl>
                </Box>
              </Grid>
            </Grid>
            
            {/* Notes Field */}
            <TextField
              label="Additional Notes"
              multiline
              rows={2}
              fullWidth
              value={formData.notes}
              onChange={(e) => setFormData(prev => ({ ...prev, notes: e.target.value }))}
              placeholder="Enter any additional information about this transfer..."
              sx={{ mt: 3 }}
            />
          </Paper>
          
          {/* Transfer Items Section */}
          <Paper elevation={1} sx={{ p: 3, borderRadius: 2 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6" color="primary" fontWeight="600">
                Transfer Items
              </Typography>
              <Button
                startIcon={<AddIcon />}
                onClick={addLine}
                variant="outlined"
                size="small"
              >
                Add Item
              </Button>
            </Box>
            <Divider sx={{ mb: 3 }} />
            
            {formData.lines.map((line, index) => (
              <Card key={index} variant="outlined" sx={{ mb: 2, borderRadius: 2 }}>
                <CardContent sx={{ p: 2 }}>
                  <Grid container spacing={2} alignItems="center">
                    <Grid item xs={12} sm={6} md={7}>
                      <FormControl fullWidth required>
                        <InputLabel>Product</InputLabel>
                        <Select
                          value={line.product}
                          label="Product"
                          onChange={(e) => handleLineChange(index, 'product', e.target.value)}
                        >
                          {products.map(product => (
                            <MenuItem key={product.id} value={product.id.toString()}>
                              <Box>
                                <Typography variant="body1" fontWeight="500">
                                  {product.name}
                                </Typography>
                                <Typography variant="caption" color="text.secondary">
                                  SKU: {product.sku}
                                </Typography>
                              </Box>
                            </MenuItem>
                          ))}
                        </Select>
                      </FormControl>
                    </Grid>
                    
                    <Grid item xs={8} sm={4} md={3}>
                      <TextField
                        label="Quantity"
                        type="number"
                        fullWidth
                        value={line.requested_qty}
                        onChange={(e) => handleLineChange(index, 'requested_qty', e.target.value)}
                        InputProps={{ 
                          inputProps: { min: 1 },
                          sx: { borderRadius: 1 }
                        }}
                      />
                    </Grid>
                    
                    <Grid item xs={4} sm={2} md={2}>
                      <IconButton
                        color="error"
                        onClick={() => removeLine(index)}
                        disabled={formData.lines.length <= 1}
                        sx={{ 
                          border: 1, 
                          borderColor: 'error.light',
                          borderRadius: 1
                        }}
                      >
                        <DeleteIcon />
                      </IconButton>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            ))}
          </Paper>
        </Box>
      </DialogContent>
      
      <DialogActions sx={{ p: 3, gap: 1 }}>
        <Button 
          onClick={onClose} 
          disabled={submitting}
          variant="outlined"
          size="large"
        >
          Cancel
        </Button>
        <Button 
          onClick={() => handleSubmit('draft')} 
          variant="outlined" 
          disabled={submitting}
          color="secondary"
          size="large"
          startIcon={submitting ? <CircularProgress size={20} /> : null}
        >
          Save as Draft
        </Button>
        <Button 
          onClick={() => handleSubmit('requested')} 
          variant="contained" 
          disabled={submitting}
          size="large"
          startIcon={submitting ? <CircularProgress size={20} /> : null}
        >
          Request Transfer
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default TransferRequestForm;