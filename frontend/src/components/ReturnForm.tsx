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
  Typography,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  FormControlLabel,
  Checkbox,
  CircularProgress,
  Alert,
} from '@mui/material';
import { saleAPI, returnAPI } from '../services/api';

interface ReturnItem {
  original_line_id: number;
  product_id: number;
  variant_id: number | null;
  quantity: number;
  unit_price: number;
  total_price: number;
  product_name: string;
  variant_name?: string;
  selected: boolean;
}

interface ReturnFormProps {
  open: boolean;
  onClose: () => void;
  saleId: number;
}

const ReturnForm: React.FC<ReturnFormProps> = ({ open, onClose, saleId }) => {
  const [sale, setSale] = useState<any>(null);
  const [items, setItems] = useState<ReturnItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [returnData, setReturnData] = useState({
    return_type: 'return',
    reason: '',
    total_amount: 0,
    refund_amount: 0,
  });

  useEffect(() => {
    if (!open || !saleId) return;

    const fetchSale = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await saleAPI.getSaleById(saleId);
        const saleData = response.data;
        
        setSale(saleData);
        
        // Initialize items from sale lines
        const initialItems: ReturnItem[] = saleData.lines.map((line: any) => ({
          original_line_id: line.id,
          product_id: line.product,
          variant_id: line.variant,
          quantity: line.quantity,
          unit_price: line.unit_price,
          total_price: line.total_price,
          product_name: line.product_name,
          variant_name: line.variant_name,
          selected: false,
        }));
        
        setItems(initialItems);
      } catch (err: any) {
        setError(err.message || 'Failed to load sale data');
        console.error('Error loading sale:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchSale();
  }, [saleId, open]);

  useEffect(() => {
    // Calculate total and refund amounts based on selected items
    const selectedItems = items.filter(item => item.selected);
    const total = selectedItems.reduce((sum, item) => sum + item.total_price, 0);
    
    setReturnData(prev => ({
      ...prev,
      total_amount: total,
      refund_amount: total,
    }));
  }, [items]);

  const handleItemSelection = (index: number, checked: boolean) => {
    const updatedItems = [...items];
    updatedItems[index].selected = checked;
    setItems(updatedItems);
  };

  const handleQuantityChange = (index: number, value: number) => {
    const updatedItems = [...items];
    const item = updatedItems[index];
    
    // Ensure quantity doesn't exceed original quantity
    const newQuantity = Math.min(value, item.quantity);
    
    updatedItems[index] = {
      ...item,
      quantity: newQuantity,
      total_price: newQuantity * item.unit_price,
    };
    
    setItems(updatedItems);
  };

  const handleSubmit = async () => {
    try {
      setLoading(true);
      setError(null);

      // Prepare return lines data
      const returnLines = items
        .filter(item => item.selected)
        .map(item => ({
          original_line_id: item.original_line_id,
          product_id: item.product_id,
          variant_id: item.variant_id,
          quantity: item.quantity,
          unit_price: item.unit_price,
          total_price: item.total_price,
        }));

      // Prepare return data
      const returnPayload = {
        original_sale: saleId,
        customer: sale.customer,
        return_type: returnData.return_type,
        reason: returnData.reason,
        total_amount: returnData.total_amount,
        refund_amount: returnData.refund_amount,
        lines: returnLines,
      };

      await returnAPI.createReturn(returnPayload);
      onClose();
    } catch (err: any) {
      setError(err.message || 'Failed to create return');
      console.error('Error creating return:', err);
    } finally {
      setLoading(false);
    }
  };

  if (loading && sale === null) {
    return (
      <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
        <DialogContent>
          <Box display="flex" justifyContent="center" alignItems="center" height="200px">
            <CircularProgress />
          </Box>
        </DialogContent>
      </Dialog>
    );
  }

  return (
    <Dialog open={open} onClose={onClose} maxWidth="md" fullWidth>
      <DialogTitle>Process Return for Sale #{sale?.receipt_number}</DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        
        <Box mb={2}>
          <FormControl fullWidth margin="normal">
            <InputLabel>Return Type</InputLabel>
            <Select
              value={returnData.return_type}
              onChange={(e) => setReturnData({...returnData, return_type: e.target.value})}
            >
              <MenuItem value="return">Return</MenuItem>
              <MenuItem value="exchange">Exchange</MenuItem>
              <MenuItem value="refund">Refund</MenuItem>
            </Select>
          </FormControl>
          
          <TextField
            fullWidth
            label="Reason"
            multiline
            rows={3}
            margin="normal"
            value={returnData.reason}
            onChange={(e) => setReturnData({...returnData, reason: e.target.value})}
          />
        </Box>

        <Typography variant="h6" gutterBottom>
          Sale Items
        </Typography>
        
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>Select</TableCell>
                <TableCell>Product</TableCell>
                <TableCell align="right">Unit Price</TableCell>
                <TableCell align="right">Qty</TableCell>
                <TableCell align="right">Total</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((item, index) => (
                <TableRow key={item.original_line_id}>
                  <TableCell padding="checkbox">
                    <Checkbox
                      checked={item.selected}
                      onChange={(e) => handleItemSelection(index, e.target.checked)}
                    />
                  </TableCell>
                  <TableCell>
                    {item.product_name}
                    {item.variant_name && ` - ${item.variant_name}`}
                  </TableCell>
                  <TableCell align="right">${item.unit_price.toFixed(2)}</TableCell>
                  <TableCell align="right">
                    {item.selected ? (
                      <TextField
                        type="number"
                        size="small"
                        value={item.quantity}
                        onChange={(e) => handleQuantityChange(index, parseInt(e.target.value) || 0)}
                        inputProps={{ min: 1, max: item.quantity }}
                        sx={{ width: '80px' }}
                      />
                    ) : (
                      item.quantity
                    )}
                  </TableCell>
                  <TableCell align="right">${item.total_price.toFixed(2)}</TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>

        <Box mt={2} p={2} bgcolor="#f5f5f5" borderRadius={1}>
          <Typography variant="h6">
            Total Amount: ${returnData.total_amount.toFixed(2)}
          </Typography>
          {returnData.return_type !== 'exchange' && (
            <Typography variant="body1">
              Refund Amount: ${returnData.refund_amount.toFixed(2)}
            </Typography>
          )}
        </Box>
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancel</Button>
        <Button 
          onClick={handleSubmit} 
          variant="contained" 
          disabled={items.filter(i => i.selected).length === 0}
        >
          Submit Return
        </Button>
      </DialogActions>
    </Dialog>
  );
};

export default ReturnForm;