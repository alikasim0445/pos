import React, { useState, useEffect } from 'react';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Button,
  Box,
  Typography,
  Chip,
  CircularProgress,
  Alert,
} from '@mui/material';
import { returnAPI } from '../services/api';

interface ReturnItem {
  id: number;
  return_number: string;
  original_sale_receipt: string;
  customer_name: string;
  return_type: string;
  status: string;
  total_amount: number;
  refund_amount: number;
  reason: string;
  created_at: string;
}

const ReturnList: React.FC = () => {
  const [returns, setReturns] = useState<ReturnItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const fetchReturns = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await returnAPI.getReturns();
        setReturns(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load returns');
        console.error('Error loading returns:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchReturns();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="200px">
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  return (
    <Box>
      <Typography variant="h5" gutterBottom>
        Returns & Exchanges
      </Typography>
      
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Return #</TableCell>
              <TableCell>Original Sale</TableCell>
              <TableCell>Customer</TableCell>
              <TableCell>Type</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Amount</TableCell>
              <TableCell>Reason</TableCell>
              <TableCell>Date</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {returns.map((ret) => (
              <TableRow key={ret.id}>
                <TableCell>{ret.return_number}</TableCell>
                <TableCell>{ret.original_sale_receipt}</TableCell>
                <TableCell>{ret.customer_name}</TableCell>
                <TableCell>
                  <Chip 
                    label={ret.return_type.charAt(0).toUpperCase() + ret.return_type.slice(1)} 
                    size="small" 
                    variant="outlined" 
                  />
                </TableCell>
                <TableCell>
                  <Chip 
                    label={ret.status.charAt(0).toUpperCase() + ret.status.slice(1)} 
                    size="small" 
                    color={
                      ret.status === 'approved' ? 'success' :
                      ret.status === 'rejected' ? 'error' :
                      ret.status === 'pending' ? 'warning' : 'default'
                    }
                  />
                </TableCell>
                <TableCell align="right">${ret.total_amount.toFixed(2)}</TableCell>
                <TableCell>{ret.reason}</TableCell>
                <TableCell>{new Date(ret.created_at).toLocaleDateString()}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
      
      {returns.length === 0 && (
        <Typography variant="body1" align="center" sx={{ mt: 2 }}>
          No returns processed yet.
        </Typography>
      )}
    </Box>
  );
};

export default ReturnList;