import React, { useState, useEffect } from 'react';
import { reservationAPI } from '../services/api';
import { Reservation } from '../types';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  CircularProgress,
  Alert,
  Fab,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  IconButton,
  Chip,
  Snackbar,
  Tooltip,
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
} from '@mui/icons-material';
import ReservationForm from '../components/ReservationForm';

const Reservations: React.FC = () => {
  const [reservations, setReservations] = useState<Reservation[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingReservation, setEditingReservation] = useState<Reservation | null>(null);
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' as 'success' | 'error' | 'warning' | 'info' });

  useEffect(() => {
    fetchReservations();
  }, []);

  const fetchReservations = async () => {
    try {
      setLoading(true);
      setError(null);
      const reservationsData = await reservationAPI.getReservations();
      setReservations(reservationsData.data);
    } catch (err: any) {
      setError(err.message || 'Failed to fetch reservations');
      console.error('Error fetching reservations:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleCreateReservation = async (reservationData: any) => {
    try {
      await reservationAPI.createReservation(reservationData);
      showSnackbar('Reservation created successfully!', 'success');
      fetchReservations();
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to create reservation', 'error');
      console.error('Error creating reservation:', err);
      throw err; // Re-throw to handle in form
    }
  };

  const handleUpdateReservation = async (reservationData: any) => {
    try {
      await reservationAPI.updateReservation(reservationData.id, reservationData);
      showSnackbar('Reservation updated successfully!', 'success');
      fetchReservations();
    } catch (err: any) {
      showSnackbar(err.message || 'Failed to update reservation', 'error');
      console.error('Error updating reservation:', err);
      throw err; // Re-throw to handle in form
    }
  };

  const handleDeleteReservation = async (reservationId: number) => {
    if (window.confirm(`Are you sure you want to delete reservation? This action cannot be undone.`)) {
      try {
        await reservationAPI.deleteReservation(reservationId);
        showSnackbar('Reservation deleted successfully!', 'success');
        fetchReservations();
      } catch (err: any) {
        showSnackbar(err.message || 'Failed to delete reservation', 'error');
        console.error('Error deleting reservation:', err);
      }
    }
  };

  const showSnackbar = (message: string, severity: 'success' | 'error' | 'info' | 'warning') => {
    setSnackbar({ open: true, message, severity });
  };

  const handleCloseSnackbar = () => {
    setSnackbar({ ...snackbar, open: false });
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
          <Typography variant="h4" gutterBottom>
            Reservations
          </Typography>
          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}
          <Box sx={{ display: 'flex', justifyContent: 'flex-end', mb: 2 }}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                setEditingReservation(null);
                setIsFormOpen(true);
              }}
            >
              New Reservation
            </Button>
          </Box>
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Reservation Number</TableCell>
                  <TableCell>User</TableCell>
                  <TableCell>Warehouse</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Expires At</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {reservations.map((reservation) => (
                  <TableRow key={reservation.id}>
                    <TableCell>{reservation.reservation_number}</TableCell>
                    <TableCell>{reservation.user_name}</TableCell>
                    <TableCell>{reservation.warehouse_name}</TableCell>
                    <TableCell>
                      <Chip label={reservation.status} color={reservation.status === 'active' ? 'success' : 'default'} />
                    </TableCell>
                    <TableCell>{new Date(reservation.expires_at).toLocaleString()}</TableCell>
                    <TableCell>
                      <Tooltip title="Edit Reservation">
                        <IconButton
                          onClick={() => {
                            setEditingReservation(reservation);
                            setIsFormOpen(true);
                          }}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Delete Reservation">
                        <IconButton onClick={() => handleDeleteReservation(reservation.id)}>
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>
      <ReservationForm
        open={isFormOpen}
        onClose={() => {
          setIsFormOpen(false);
          setEditingReservation(null);
        }}
        onSubmit={editingReservation ? handleUpdateReservation : handleCreateReservation}
        initialData={editingReservation}
        isEditing={!!editingReservation}
      />
      <Snackbar
        open={snackbar.open}
        autoHideDuration={6000}
        onClose={handleCloseSnackbar}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'right' }}
      >
        <Alert onClose={handleCloseSnackbar} severity={snackbar.severity} sx={{ width: '100%' }}>
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Reservations;