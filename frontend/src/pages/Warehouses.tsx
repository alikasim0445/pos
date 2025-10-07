import React, { useEffect, useState } from 'react';
import { useAppSelector } from '../hooks/redux';
import { warehouseAPI } from '../services/api';
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
} from '@mui/material';
import { Add as AddIcon, Edit as EditIcon } from '@mui/icons-material';

const Warehouses: React.FC = () => {
    const [warehouses, setWarehouses] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingWarehouse, setEditingWarehouse] = useState<any>(null);
    const { isAuthenticated } = useAppSelector((state) => state.auth);

    useEffect(() => {
        const fetchWarehouses = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await warehouseAPI.getWarehouses();
                setWarehouses(response.data);
            } catch (err: any) {
                setError(err.message || 'Failed to load warehouses');
            } finally {
                setLoading(false);
            }
        };

        if (isAuthenticated) {
            fetchWarehouses();
        }
    }, [isAuthenticated, isFormOpen]); // Add isFormOpen to refresh when form closes

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
            // Update existing warehouse in the list
            setWarehouses(prev => prev.map(w => w.id === warehouse.id ? warehouse : w));
        } else {
            // Add new warehouse to the list
            setWarehouses(prev => [warehouse, ...prev]);
        }
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
                    <Grid item xs={12} sm={6} md={4} key={warehouse.id}>
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
                                    <IconButton 
                                        size="small" 
                                        onClick={() => handleEditWarehouse(warehouse)}
                                    >
                                        <EditIcon fontSize="small" />
                                    </IconButton>
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
        </div>
    );
};

export default Warehouses;