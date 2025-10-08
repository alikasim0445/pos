import React, { useState, useEffect } from 'react';
import { useAppSelector } from '../hooks/redux';
import { transferAPI } from '../services/api';
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
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogContentText,
  DialogTitle,
  IconButton,
} from '@mui/material';
import { Transfer } from '../types';
import { Check as CheckIcon, Clear as ClearIcon, Visibility as VisibilityIcon } from '@mui/icons-material';

interface TransferApprovalProps {
  onTransferUpdate?: () => void;
}

const TransferApproval: React.FC<TransferApprovalProps> = ({ onTransferUpdate }) => {
  const [transfers, setTransfers] = useState<Transfer[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [selectedTransfer, setSelectedTransfer] = useState<Transfer | null>(null);
  const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
  const [rejectionDialogOpen, setRejectionDialogOpen] = useState(false);
  const [dialogLoading, setDialogLoading] = useState(false);
  const [dialogError, setDialogError] = useState<string | null>(null);

  const { user, token } = useAppSelector((state) => state.auth);

  useEffect(() => {
    fetchPendingTransfers();
  }, []);

  const fetchPendingTransfers = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await transferAPI.getTransfers();
      // Filter to only show transfers with status 'requested'
      const pendingTransfers = response.data.filter((transfer: Transfer) => transfer.status === 'requested');
      setTransfers(pendingTransfers);
    } catch (err: any) {
      setError(err.message || 'Failed to load pending transfers');
      console.error('Error loading pending transfers:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleApproveTransfer = async () => {
    if (!selectedTransfer || !user) return;

    try {
      setDialogLoading(true);
      setDialogError(null);

      // Update the transfer status to 'approved'
      const updatedTransfer = {
        ...selectedTransfer,
        status: 'approved'
      };

      await transferAPI.updateTransfer(selectedTransfer.id, updatedTransfer);
      
      // Refresh the list of transfers
      fetchPendingTransfers();
      if (onTransferUpdate) onTransferUpdate();
      
      // Close dialog
      setApprovalDialogOpen(false);
      setSelectedTransfer(null);
    } catch (err: any) {
      setDialogError(err.message || 'Failed to approve transfer');
      console.error('Error approving transfer:', err);
    } finally {
      setDialogLoading(false);
    }
  };

  const handleRejectTransfer = async () => {
    if (!selectedTransfer || !user) return;

    try {
      setDialogLoading(true);
      setDialogError(null);

      // Update the transfer status to 'rejected'
      const updatedTransfer = {
        ...selectedTransfer,
        status: 'rejected'
      };

      await transferAPI.updateTransfer(selectedTransfer.id, updatedTransfer);
      
      // Refresh the list of transfers
      fetchPendingTransfers();
      if (onTransferUpdate) onTransferUpdate();
      
      // Close dialog
      setRejectionDialogOpen(false);
      setSelectedTransfer(null);
    } catch (err: any) {
      setDialogError(err.message || 'Failed to reject transfer');
      console.error('Error rejecting transfer:', err);
    } finally {
      setDialogLoading(false);
    }
  };

  const handleViewDetails = (transfer: Transfer) => {
    setSelectedTransfer(transfer);
    // For now, just show an alert with details since we don't have a detailed view yet
    alert(`Transfer Details:\nTransfer # ${transfer.transfer_number}\nFrom: ${transfer.from_warehouse?.name || 'N/A'}\nTo: ${transfer.to_warehouse?.name || 'N/A'}\nItems: ${transfer.lines?.length || 0}\nNotes: ${transfer.notes || 'N/A'}`);
  };

  const handleApproveClick = (transfer: Transfer) => {
    setSelectedTransfer(transfer);
    setApprovalDialogOpen(true);
  };

  const handleRejectClick = (transfer: Transfer) => {
    setSelectedTransfer(transfer);
    setRejectionDialogOpen(true);
  };

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
      <Typography variant="h6" gutterBottom>
        Pending Transfers for Approval
      </Typography>
      
      {transfers.length === 0 ? (
        <Typography variant="body1" align="center" sx={{ mt: 2, py: 4 }}>
          No pending transfers to approve.
        </Typography>
      ) : (
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Transfer #</TableCell>
                <TableCell>From Warehouse</TableCell>
                <TableCell>To Warehouse</TableCell>
                <TableCell>Requested By</TableCell>
                <TableCell>Items</TableCell>
                <TableCell>Date</TableCell>
                <TableCell>Status</TableCell>
                <TableCell align="center">Actions</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {transfers.map((transfer) => (
                <TableRow key={transfer.id}>
                  <TableCell>{transfer.transfer_number}</TableCell>
                  <TableCell>{transfer.from_warehouse?.name || 'N/A'}</TableCell>
                  <TableCell>{transfer.to_warehouse?.name || 'N/A'}</TableCell>
                  <TableCell>{transfer.requested_by?.first_name ? `${transfer.requested_by.first_name} ${transfer.requested_by.last_name}` : transfer.requested_by?.username || 'N/A'}</TableCell>
                  <TableCell>{transfer.lines?.length || 0}</TableCell>
                  <TableCell>{transfer.requested_at ? new Date(transfer.requested_at).toLocaleDateString() : 'N/A'}</TableCell>
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
                  <TableCell align="center">
                    <IconButton 
                      color="primary" 
                      size="small"
                      onClick={() => handleViewDetails(transfer)}
                      title="View Details"
                    >
                      <VisibilityIcon />
                    </IconButton>
                    <IconButton 
                      color="success" 
                      size="small"
                      onClick={() => handleApproveClick(transfer)}
                      title="Approve Transfer"
                    >
                      <CheckIcon />
                    </IconButton>
                    <IconButton 
                      color="error" 
                      size="small"
                      onClick={() => handleRejectClick(transfer)}
                      title="Reject Transfer"
                    >
                      <ClearIcon />
                    </IconButton>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      {/* Approval Confirmation Dialog */}
      <Dialog
        open={approvalDialogOpen}
        onClose={() => setApprovalDialogOpen(false)}
        aria-labelledby="approval-dialog-title"
        aria-describedby="approval-dialog-description"
      >
        <DialogTitle id="approval-dialog-title">Approve Transfer</DialogTitle>
        <DialogContent>
          <DialogContentText id="approval-dialog-description">
            Are you sure you want to approve transfer <strong>{selectedTransfer?.transfer_number}</strong>?
            This action cannot be undone.
          </DialogContentText>
          {dialogError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {dialogError}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setApprovalDialogOpen(false)} 
            disabled={dialogLoading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleApproveTransfer} 
            variant="contained" 
            color="success"
            disabled={dialogLoading}
          >
            {dialogLoading ? 'Approving...' : 'Approve'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Rejection Confirmation Dialog */}
      <Dialog
        open={rejectionDialogOpen}
        onClose={() => setRejectionDialogOpen(false)}
        aria-labelledby="rejection-dialog-title"
        aria-describedby="rejection-dialog-description"
      >
        <DialogTitle id="rejection-dialog-title">Reject Transfer</DialogTitle>
        <DialogContent>
          <DialogContentText id="rejection-dialog-description">
            Are you sure you want to reject transfer <strong>{selectedTransfer?.transfer_number}</strong>?
            This action cannot be undone.
          </DialogContentText>
          {dialogError && (
            <Alert severity="error" sx={{ mt: 2 }}>
              {dialogError}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button 
            onClick={() => setRejectionDialogOpen(false)} 
            disabled={dialogLoading}
          >
            Cancel
          </Button>
          <Button 
            onClick={handleRejectTransfer} 
            variant="contained" 
            color="error"
            disabled={dialogLoading}
          >
            {dialogLoading ? 'Rejecting...' : 'Reject'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default TransferApproval;