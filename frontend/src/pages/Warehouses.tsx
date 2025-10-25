import React, { useEffect, useState } from 'react';
import { useAppSelector, useAppDispatch } from '../hooks/redux';
import { warehouseAPI } from '../services/api';
import { setWarehouses, addWarehouse, updateWarehouse, deleteWarehouse, setLoading, setError } from '../store/warehousesSlice';
import realTimeSyncService from '../services/realTimeSyncService';
import WarehouseForm from '../components/WarehouseForm';
import {
  CircularProgress,
  Alert,
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
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material';

const Warehouses: React.FC = () => {
    const dispatch = useAppDispatch();
    const { warehouses, loading, error } = useAppSelector((state) => state.warehouses);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingWarehouse, setEditingWarehouse] = useState<any>(null);
    const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
    const [warehouseToDelete, setWarehouseToDelete] = useState<{id: number, name: string} | null>(null);
    const { isAuthenticated } = useAppSelector((state) => state.auth);

    useEffect(() => {
        const fetchWarehouses = async () => {
            dispatch(setLoading(true));
            dispatch(setError(null));
            
            try {
                const response = await warehouseAPI.getWarehouses();
                dispatch(setWarehouses(response.data));
            } catch (err: any) {
                dispatch(setError(err.message || 'Failed to load warehouses'));
            } finally {
                dispatch(setLoading(false));
            }
        };

        if (isAuthenticated) {
            fetchWarehouses();
        }
    }, [isAuthenticated, dispatch]);

    // Initialize and connect to real-time sync
    useEffect(() => {
        if (isAuthenticated) {
            realTimeSyncService.connect();
        }

        return () => {
            realTimeSyncService.disconnect();
        };
    }, [isAuthenticated]);

    const handleCreateWarehouse = () => {
        setEditingWarehouse(null);
        setIsFormOpen(true);
    };

    const handleEditWarehouse = (warehouse: any) => {
        setEditingWarehouse(warehouse);
        setIsFormOpen(true);
    };

    const handleFormSubmit = (warehouse: any) => {
        if (editingWarehouse) {
            // Update existing warehouse
            dispatch(updateWarehouse(warehouse));
            realTimeSyncService.sendWarehouseUpdate('update', warehouse);
        } else {
            // Add new warehouse to local state first for immediate UI update
            // Then send to WebSocket to sync with other clients
            dispatch(addWarehouse(warehouse));
            realTimeSyncService.sendWarehouseUpdate('create', warehouse);
        }
        
        setIsFormOpen(false);
    };

    const handleDeleteClick = (warehouse: any) => {
        setWarehouseToDelete({id: warehouse.id, name: warehouse.name});
        setDeleteDialogOpen(true);
    };

    const handleDeleteConfirm = () => {
        if (warehouseToDelete) {
            dispatch(deleteWarehouse(warehouseToDelete.id));
            realTimeSyncService.sendWarehouseUpdate('delete', { id: warehouseToDelete.id });
            setDeleteDialogOpen(false);
            setWarehouseToDelete(null);
        }
    };

    const handleDeleteCancel = () => {
        setDeleteDialogOpen(false);
        setWarehouseToDelete(null);
    };

    if (loading) {
        return (
            <div className="flex justify-center items-center h-64">
                <CircularProgress />
            </div>
        );
    }

    if (error) {
        return (
            <div className="container mx-auto px-4 py-8">
                <Alert severity="error">{error}</Alert>
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8">
            <h1 className="text-3xl font-bold text-gray-800 mb-6">Warehouses</h1>
            <Grid container spacing={3}>
                {warehouses.map((warehouse: any) => (
                    <Grid xs={12} sm={6} md={4} key={warehouse.id}>
                        <Card>
                            <CardContent>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                                    <div>
                                        <Typography variant="h6" component="h2">
                                            {warehouse.name}
                                        </Typography>
                                        <Typography color="textSecondary">
                                            {warehouse.location}
                                        </Typography>
                                        <Typography>
                                            Capacity: {warehouse.capacity}
                                        </Typography>
                                        {warehouse.contact_person && (
                                            <Typography>
                                                Contact: {warehouse.contact_person}
                                            </Typography>
                                        )}
                                    </div>
                                    <div>
                                        <IconButton 
                                            size="small" 
                                            onClick={() => handleEditWarehouse(warehouse)}
                                            color="primary"
                                        >
                                            <EditIcon fontSize="small" />
                                        </IconButton>
                                        <IconButton 
                                            size="small" 
                                            onClick={() => handleDeleteClick(warehouse)}
                                            color="error"
                                        >
                                            <DeleteIcon fontSize="small" />
                                        </IconButton>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </Grid>
                ))}
            </Grid>
            
            {/* Add Warehouse Floating Action Button */}
            <Fab 
                color="primary" 
                aria-label="add" 
                style={{ position: 'fixed', bottom: 16, right: 16 }}
                onClick={handleCreateWarehouse}
            >
                <AddIcon />
            </Fab>
            
            {/* Warehouse Form Modal */}
            <WarehouseForm 
                open={isFormOpen}
                onClose={() => setIsFormOpen(false)}
                onSubmit={handleFormSubmit}
                initialData={editingWarehouse}
            />

            {/* Delete Confirmation Dialog */}
            <Dialog
                open={deleteDialogOpen}
                onClose={handleDeleteCancel}
                aria-labelledby="delete-warehouse-dialog-title"
                aria-describedby="delete-warehouse-dialog-description"
            >
                <DialogTitle id="delete-warehouse-dialog-title">
                    {"Confirm Delete"}
                </DialogTitle>
                <DialogContent>
                    <DialogContentText id="delete-warehouse-dialog-description">
                        {warehouseToDelete && (
                            `Are you sure you want to delete the warehouse "${warehouseToDelete.name}"? This action cannot be undone.`
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
        </div>
    );
};

export default Warehouses;