import React, { useState, useEffect } from 'react';
import { reportAPI } from '../services/api';
import { useAppSelector } from '../hooks/redux';
import {
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Typography,
  Box,
  Alert,
  CircularProgress,
  Chip,
} from '@mui/material';

interface TransferReportItem {
  id: number;
  transfer_number: string;
  from_warehouse: string;
  to_warehouse: string;
  status: string;
  requested_at: string;
  approved_at: string | null;
  received_at: string | null;
  notes: string;
  items: Array<{
    product_name: string;
    requested_qty: number;
    transferred_qty: number;
    received_qty: number;
  }>;
}

interface TransferReportProps {
  filters: {
    startDate: string;
    endDate: string;
    warehouseId: string;
    categoryId: string;
  };
}

const TransferReport: React.FC<TransferReportProps> = ({ filters }) => {
  const [reportData, setReportData] = useState<TransferReportItem[]>([]);
  const [summary, setSummary] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    const fetchReport = async () => {
      try {
        setLoading(true);
        setError(null);
        
        const params: any = {};
        if (filters.startDate) params.start_date = filters.startDate;
        if (filters.endDate) params.end_date = filters.endDate;
        
        const response = await reportAPI.getTransferReport(params);
        setReportData(response.data.transfers);
        setSummary(response.data.summary);
      } catch (err: any) {
        setError(err.message || 'Failed to load transfer report');
        console.error('Error loading transfer report:', err);
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchReport();
    }
  }, [filters, isAuthenticated]);

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
      <Box mb={3}>
        <Typography variant="h6">Transfer Report Summary</Typography>
        {summary && (
          <Box display="flex" gap={3} mb={2}>
            <Chip label={`Total Transfers: ${summary.total_transfers}`} variant="outlined" />
            <Chip label={`Period: ${summary.date_range}`} variant="outlined" />
          </Box>
        )}
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Transfer #</TableCell>
              <TableCell>From</TableCell>
              <TableCell>To</TableCell>
              <TableCell>Status</TableCell>
              <TableCell>Date</TableCell>
              <TableCell>Items</TableCell>
              <TableCell>Notes</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {reportData.map((transfer) => (
              <TableRow key={transfer.id}>
                <TableCell>{transfer.transfer_number}</TableCell>
                <TableCell>{transfer.from_warehouse}</TableCell>
                <TableCell>{transfer.to_warehouse}</TableCell>
                <TableCell>
                  <Chip 
                    label={transfer.status} 
                    size="small" 
                    color={
                      transfer.status === 'received' ? 'success' :
                      transfer.status === 'in_transit' ? 'info' :
                      transfer.status === 'approved' ? 'primary' :
                      transfer.status === 'requested' ? 'warning' :
                      transfer.status === 'rejected' ? 'error' : 'default'
                    }
                  />
                </TableCell>
                <TableCell>{new Date(transfer.requested_at).toLocaleDateString()}</TableCell>
                <TableCell>
                  {transfer.items.map((item, idx) => (
                    <div key={idx}>
                      {item.requested_qty}x {item.product_name}
                    </div>
                  ))}
                </TableCell>
                <TableCell>{transfer.notes}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {reportData.length === 0 && (
        <Typography variant="body1" align="center" sx={{ mt: 2 }}>
          No transfers found for the selected criteria.
        </Typography>
      )}
    </Box>
  );
};

export default TransferReport;