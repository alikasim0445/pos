import React, { useEffect, useState } from 'react';
import { useAppSelector } from '../hooks/redux';
import { productAPI } from '../services/api';
import ProductList from '../components/ProductList';
import ProductForm from '../components/ProductForm';
import {
  CircularProgress,
  Alert,
  Fab,
} from '@mui/material';
import { Add as AddIcon } from '@mui/icons-material';

const Products = () => {
    const [products, setProducts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isFormOpen, setIsFormOpen] = useState(false);
    const [editingProduct, setEditingProduct] = useState<any>(null);
    const { isAuthenticated } = useAppSelector((state) => state.auth);

    useEffect(() => {
        const fetchProducts = async () => {
            try {
                setLoading(true);
                setError(null);
                const response = await productAPI.getProducts();
                setProducts(response.data);
            } catch (err: any) {
                setError(err.message || 'Failed to load products');
            } finally {
                setLoading(false);
            }
        };

        if (isAuthenticated) {
            fetchProducts();
        }
    }, [isAuthenticated, isFormOpen]); // Add isFormOpen to refresh when form closes

    const handleCreateProduct = () => {
        setEditingProduct(null);
        setIsFormOpen(true);
    };

    const handleEditProduct = (product: any) => {
        setEditingProduct(product);
        setIsFormOpen(true);
    };

    const handleFormSubmit = (product: any) => {
        if (editingProduct) {
            // Update existing product in the list
            setProducts(prev => prev.map(p => p.id === product.id ? product : p));
        } else {
            // Add new product to the list
            setProducts(prev => [product, ...prev]);
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
            <h1 className="text-3xl font-bold text-gray-800 mb-6">Products</h1>
            <div className="bg-white rounded-lg shadow-md p-6">
                <ProductList products={products} onEdit={handleEditProduct} />
            </div>
            
            {/* Add Product Floating Action Button */}
            <Fab 
                color="primary" 
                aria-label="add" 
                style={{ position: 'fixed', bottom: 16, right: 16 }}
                onClick={handleCreateProduct}
            >
                <AddIcon />
            </Fab>
            
            {/* Product Form Modal */}
            <ProductForm 
                open={isFormOpen}
                onClose={() => setIsFormOpen(false)}
                onSubmit={handleFormSubmit}
                initialData={editingProduct}
            />
        </div>
    );
};

export default Products;