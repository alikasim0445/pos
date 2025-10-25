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
import { productAPI, warehouseAPI, locationAPI, binAPI, inventoryAPI } from '../services/api';

interface InventoryFormProps {
  open: boolean;
  onClose: () => void;
  onSubmit: (inventory: any) => void;
  initialData?: any;
}

const InventoryForm: React.FC<InventoryFormProps> = ({ open, onClose, onSubmit, initialData }) => {
  const [formData, setFormData] = useState({
    product: '',
    variant: '',
    warehouse: '',
    location: '',
    bin: '',
    bin_location: '',
    qty_on_hand: '0',
    qty_reserved: '0',
    min_stock_level: '0'
  });
  
  const [products, setProducts] = useState([]);
  const [warehouses, setWarehouses] = useState([]);
  const [locations, setLocations] = useState([]);
  const [bins, setBins] = useState([]);
  const [loading, setLoading] = useState(false);
  const [loadingProducts, setLoadingProducts] = useState(true);
  const [loadingWarehouses, setLoadingWarehouses] = useState(true);
  const [loadingLocations, setLoadingLocations] = useState(false);
  const [loadingBins, setLoadingBins] = useState(false);

  useEffect(() => {
    if (open) {
      loadProducts();
      loadWarehouses();
      if (initialData) {
        setFormData({
          product: initialData.product?.toString() || '',
          variant: initialData.variant?.toString() || '',
          warehouse: initialData.warehouse?.toString() || '',
          location: initialData.location?.toString() || '',
          bin: initialData.bin?.toString() || '',
          bin_location: initialData.bin_location || '',
          qty_on_hand: initialData.qty_on_hand?.toString() || '0',
          qty_reserved: initialData.qty_reserved?.toString() || '0',
          min_stock_level: initialData.min_stock_level?.toString() || '0'
        });
        
        // Load locations and bins based on the initial warehouse
        if (initialData.warehouse) {
          loadLocations(initialData.warehouse.toString());
          if (initialData.location) {
            loadBins(initialData.location.toString());
          }
        }
      } else {
        resetForm();
      }
    }
  }, [open, initialData]);

  const resetForm = () => {
    setFormData({
      product: '',
      variant: '',
      warehouse: '',
      location: '',
      bin: '',
      bin_location: '',
      qty_on_hand: '0',
      qty_reserved: '0',
      min_stock_level: '0'
    });
    setLocations([]);
    setBins([]);
  };

  const loadProducts = async () => {
    try {
      setLoadingProducts(true);
      const response = await productAPI.getProducts();
      setProducts(response.data);
    } catch (error) {
      console.error('Failed to load products:', error);
    } finally {
      setLoadingProducts(false);
    }
  };

  const loadWarehouses = async () => {
    try {
      setLoadingWarehouses(true);
      const response = await warehouseAPI.getWarehouses();
      setWarehouses(response.data);
    } catch (error) {
      console.error('Failed to load warehouses:', error);
    } finally {
      setLoadingWarehouses(false);
    }
  };

  const loadLocations = async (warehouseId: string) => {
    if (!warehouseId) {
      setLocations([]);
      return;
    }
    
    try {
      setLoadingLocations(true);
      const response = await locationAPI.getLocationsByWarehouse(warehouseId);
      console.log('Loaded locations for warehouse:', warehouseId, response.data);
      setLocations(response.data);
    } catch (error) {
      console.error('Failed to load locations:', error);
      setLocations([]);
    } finally {
      setLoadingLocations(false);
    }
  };

  const loadBins = async (locationId: string) => {
    if (!locationId) {
      setBins([]);
      return;
    }
    
    try {
      setLoadingBins(true);
      const response = await binAPI.getBinsByLocation(locationId);
      setBins(response.data);
    } catch (error) {
      console.error('Failed to load bins:', error);
      setBins([]);
    } finally {
      setLoadingBins(false);
    }
  };


  const handleSelectChange = (name: string, value: string) => {
    setFormData(prev => {
      const newState = { ...prev, [name]: value };
      
      if (name === 'warehouse') {
        newState.location = '';
        newState.bin = '';
        setLocations([]);
        setBins([]);
        if (value) {
          loadLocations(value);
        }
      } else if (name === 'location') {
        newState.bin = '';
        setBins([]);
        if (value) {
          loadBins(value);
        }
      }
      
      return newState;
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
      // Check if any loading operations are in progress
      if (loadingProducts || loadingWarehouses || loadingLocations || loadingBins) {
        alert('Please wait for all data to load before submitting.');
        setLoading(false);
        return;
      }
      
      // Validate required fields
      const productId = parseInt(formData.product);
      const warehouseId = parseInt(formData.warehouse);
      
      if (isNaN(productId) || productId <= 0) {
        alert('Please select a valid product');
        setLoading(false);
        return;
      }
      
      if (isNaN(warehouseId) || warehouseId <= 0) {
        alert('Please select a valid warehouse');
        setLoading(false);
        return;
      }
      
      // Validate location/warehouse consistency
      let validatedLocationId = null;
      if (formData.location) {
        const locationId = parseInt(formData.location);
        // Check if the selected location is in the currently loaded locations list
        const selectedLocation = locations.find((loc: any) => loc.id === locationId);
        if (locations.length > 0 && !selectedLocation) {
          alert('Selected location does not belong to the selected warehouse. Please select a location from the current warehouse.');
          setLoading(false);
          return;
        }
        validatedLocationId = locationId;
      }
      
      // Validate bin/location consistency
      let validatedBinId = null;
      if (formData.bin && formData.location) {
        const binId = parseInt(formData.bin);
        const locationId = parseInt(formData.location);
        // Check if the selected bin is in the currently loaded bins list
        const selectedBin = bins.find((bin: any) => bin.id === binId);
        if (bins.length > 0 && !selectedBin) {
          alert('Selected bin does not belong to the selected location. Please select a bin from the current location.');
          setLoading(false);
          return;
        }
        validatedBinId = binId;
      }

      // Convert numeric fields
      const inventoryData: any = {
        product: productId,
        variant: formData.variant ? parseInt(formData.variant) : null,
        warehouse: warehouseId,
        location: validatedLocationId,
        bin: validatedBinId,
        bin_location: formData.bin_location || '',
        qty_on_hand: parseInt(formData.qty_on_hand) || 0,
        qty_reserved: parseInt(formData.qty_reserved) || 0,
        min_stock_level: parseInt(formData.min_stock_level) || 0
      };
      
      if (initialData && initialData.id) {
        // Update existing inventory
        const response = await inventoryAPI.updateInventory(initialData.id, inventoryData);
        onSubmit(response.data);
      } else {
        // Create new inventory record
        const response = await inventoryAPI.createInventory(inventoryData);
        onSubmit(response.data);
      }
      
      onClose();
    } catch (error) {
      console.error('Failed to save inventory:', error);
      
      // Try to extract and display error details from the response
      if (error.response && error.response.data) {
        console.error('Backend validation errors:', error.response.data);
        const errorData = error.response.data;
        if (typeof errorData === 'object') {
          let errorMessage = 'Validation errors occurred:\n';
          for (const [field, messages] of Object.entries(errorData)) {
            if (Array.isArray(messages)) {
              errorMessage += `${field}: ${messages.join(', ')}\n`;
            } else {
              errorMessage += `${field}: ${messages}\n`;
            }
          }
          alert(errorMessage);
        } else {
          alert(`Error: ${errorData}`);
        }
      } else {
        console.error('Request error:', error);
        alert('An unexpected error occurred while saving inventory');
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>
        {initialData ? 'Edit Inventory' : 'Add Inventory'}
      </DialogTitle>
      <DialogContent>
        <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2, mt: 2 }}>
          {(loadingProducts || loadingWarehouses) ? (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
              <CircularProgress />
            </Box>
          ) : (
            <>
              <FormControl fullWidth>
                <InputLabel>Product</InputLabel>
                <Select
                  name="product"
                  value={formData.product}
                  label="Product"
                  onChange={(e) => handleSelectChange('product', e.target.value)}
                >
                  {products.map((product: any) => (
                    <MenuItem key={product.id} value={product.id.toString()}>
                      {product.name} ({product.sku})
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <FormControl fullWidth>
                <InputLabel>Warehouse</InputLabel>
                <Select
                  name="warehouse"
                  value={formData.warehouse}
                  label="Warehouse"
                  onChange={(e) => handleSelectChange('warehouse', e.target.value)}
                >
                  {warehouses.map((warehouse: any) => (
                    <MenuItem key={warehouse.id} value={warehouse.id.toString()}>
                      {warehouse.name} - {warehouse.location}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              
              <FormControl fullWidth>
                <InputLabel>Location</InputLabel>
                <Select
                  name="location"
                  value={formData.location}
                  label="Location"
                  onChange={(e) => handleSelectChange('location', e.target.value)}
                  disabled={loadingLocations || !formData.warehouse}
                >
                  {loadingLocations ? (
                    <MenuItem disabled>Loading locations...</MenuItem>
                  ) : locations.length === 0 ? (
                    <MenuItem disabled>
                      {formData.warehouse ? 'No locations available (optional field)' : 'Select a warehouse first'}
                    </MenuItem>
                  ) : (
                    locations.map((location: any) => (
                      <MenuItem key={location.id} value={location.id.toString()}>
                        {location.name} - {location.code} ({location.warehouse_name})
                      </MenuItem>
                    ))
                  )}
                </Select>
              </FormControl>
              
              <FormControl fullWidth>
                <InputLabel>Bin</InputLabel>
                <Select
                  name="bin"
                  value={formData.bin}
                  label="Bin"
                  onChange={(e) => handleSelectChange('bin', e.target.value)}
                  disabled={loadingBins || !formData.location}
                >
                  {loadingBins ? (
                    <MenuItem disabled>Loading bins...</MenuItem>
                  ) : bins.length === 0 ? (
                    <MenuItem disabled>
                      {formData.location ? 'No bins available (optional field)' : 'Select a location first'}
                    </MenuItem>
                  ) : (
                    bins.map((bin: any) => (
                      <MenuItem key={bin.id} value={bin.id.toString()}>
                        {bin.name} - {bin.code} ({bin.location_name})
                      </MenuItem>
                    ))
                  )}
                </Select>
              </FormControl>
              
              <TextField
                margin="dense"
                name="bin_location"
                label="Legacy Bin/Location"
                type="text"
                fullWidth
                variant="outlined"
                placeholder="e.g., A-1-3 (for legacy systems)"
                value={formData.bin_location}
                onChange={handleChange}
                helperText="Optional legacy field, use Location/ Bin fields above for proper tracking"
              />
              
              <TextField
                margin="dense"
                name="qty_on_hand"
                label="Quantity On Hand"
                type="number"
                fullWidth
                variant="outlined"
                value={formData.qty_on_hand}
                onChange={handleChange}
              />
              
              <TextField
                margin="dense"
                name="qty_reserved"
                label="Quantity Reserved"
                type="number"
                fullWidth
                variant="outlined"
                value={formData.qty_reserved}
                onChange={handleChange}
              />
              
              <TextField
                margin="dense"
                name="min_stock_level"
                label="Minimum Stock Level"
                type="number"
                fullWidth
                variant="outlined"
                value={formData.min_stock_level}
                onChange={handleChange}
              />
            </>
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

export default InventoryForm;