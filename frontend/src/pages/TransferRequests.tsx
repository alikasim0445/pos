import React, { useState, useEffect } from 'react';
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import { transferAPI } from '../services/api';
import TransferRequestForm from '../components/TransferRequestForm';
import {
  Box,
  Fab,
  Card,
  CardContent,
  Typography,
  Grid,
  IconButton,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  Button,
  Alert,
  CircularProgress,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon, Visibility as VisibilityIcon } from '@mui/icons-material';
import { Transfer } from '../types';

const TransferRequests: React.FC = () => {
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [transferToDelete, setTransferToDelete] = useState<{id: number, transfer_number: string} | null>(null);
  const { isAuthenticated } = useAppSelector((state) => state.auth);

  useEffect(() => {
    const fetchTransfers = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await transferAPI.getTransfers();
        setTransfers(response.data);
      } catch (err: any) {
        setError(err.message || 'Failed to load transfers');
      } finally {
        setLoading(false);
      }
    };

    if (isAuthenticated) {
      fetchTransfers();
    }
  }, [isAuthenticated]);

  const handleCreateTransfer = () => {
    setIsFormOpen(true);
  };

  const handleFormSubmit = (newTransfer: Transfer) => {
    setTransfers(prev => [newTransfer, ...prev]);
    setIsFormOpen(false);
  };

  const handleDeleteClick = (transfer: Transfer) => {
    setTransferToDelete({id: transfer.id, transfer_number: transfer.transfer_number});
    setDeleteDialogOpen(true);
  };

  const handleDeleteConfirm = async () => {
    if (transferToDelete) {
      try {
        await transferAPI.deleteTransfer(transferToDelete.id);
        setTransfers(prev => prev.filter(t => t.id !== transferToDelete.id));
        setDeleteDialogOpen(false);
        setTransferToDelete(null);
      } catch (err: any) {
        setError(err.message || 'Failed to delete transfer');
        setDeleteDialogOpen(false);
        setTransferToDelete(null);
      }
    }
  };

  const handleDeleteCancel = () => {
    setDeleteDialogOpen(false);
    setTransferToDelete(null);
  };

  // Function to get status chip color based on status
  const getStatusColor = (status: string) => {
    switch (status) {
      case 'received': return 'success';
      case 'in_transit': return 'info';
      case 'approved': return 'primary';
      case 'requested': return 'warning';
      case 'rejected': return 'error';
      case 'draft': return 'default';
      case 'cancelled': return 'secondary';
      default: return 'default';
    }
  };

  const getStatusLabel = (status: string) => {
    switch (status) {
      case 'draft': return 'Draft';
      case 'requested': return 'Requested';
      case 'approved': return 'Approved';
      case 'in_transit': return 'In Transit';
      case 'received': return 'Received';
      case 'rejected': return 'Rejected';
      case 'cancelled': return 'Cancelled';
      default: return status;
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ p: 3 }}>
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
            <Typography variant="h5">Transfer Requests</Typography>
            <Fab 
              color="primary" 
              aria-label="create transfer"
              onClick={handleCreateTransfer}
            >
              <AddIcon />
            </Fab>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Transfer #</TableCell>
                  <TableCell>From Warehouse</TableCell>
                  <TableCell>To Warehouse</TableCell>
                  <TableCell>Items</TableCell>
                  <TableCell>Date</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell align="center">Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {transfers.length === 0 ? (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      No transfer requests found
                    </TableCell>
                  </TableRow>
                ) : (
                  transfers.map((transfer) => (
                    <TableRow key={transfer.id}>
                      <TableCell>{transfer.transfer_number}</TableCell>
                      <TableCell>{transfer.from_warehouse?.name || 'N/A'}</TableCell>
                      <TableCell>{transfer.to_warehouse?.name || 'N/A'}</TableCell>
                      <TableCell>{transfer.lines?.length || 0}</TableCell>
                      <TableCell>{transfer.requested_at ? new Date(transfer.requested_at).toLocaleDateString() : 'N/A'}</TableCell>
                      <TableCell>
                        <Chip 
                          label={getStatusLabel(transfer.status)} 
                          size="small"
                          color={getStatusColor(transfer.status)}
                        />
                      </TableCell>
                      <TableCell align="center">
                        <IconButton 
                          color="primary" 
                          size="small"
                          onClick={() => alert(`Transfer Details: ${JSON.stringify(transfer, null, 2)}`)}
                          title="View Details"
                        >
                          <VisibilityIcon />
                        </IconButton>
                        <IconButton 
                          color="secondary" 
                          size="small"
                          onClick={() => alert(`Edit functionality would go here for transfer ${transfer.transfer_number}`)}
                          title="Edit Transfer"
                        >
                          <EditIcon />
                        </IconButton>
                        <IconButton 
                          color="error" 
                          size="small"
                          onClick={() => handleDeleteClick(transfer)}
                          title="Delete Transfer"
                        >
                          <DeleteIcon />
                        </IconButton>
                      </TableCell>
                    </TableRow>
                  ))
                )}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Form Modal */}
      <TransferRequestForm 
        open={isFormOpen}
        onClose={() => setIsFormOpen(false)}
        onSubmit={handleFormSubmit}
      />

      {/* Delete Confirmation Dialog */}
      <Dialog
        open={deleteDialogOpen}
        onClose={handleDeleteCancel}
        aria-labelledby="delete-transfer-dialog-title"
        aria-describedby="delete-transfer-dialog-description"
      >
        <DialogTitle id="delete-transfer-dialog-title">
          {"Confirm Delete"}
        </DialogTitle>
        <DialogContent>
          <DialogContentText id="delete-transfer-dialog-description">
            {transferToDelete && (
              `Are you sure you want to delete transfer "${transferToDelete.transfer_number}"? This action cannot be undone.`
            )}
          </DialogContentText>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleDeleteCancel}>Cancel</Button>
          <Button onClick={handleDeleteConfirm} color="error" variant="contained">
            Delete
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TransferRequests;