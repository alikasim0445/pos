import axios from 'axios';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

const apiClient = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Authentication
export const login = async (credentials) => {
  const response = await apiClient.post('/auth/login', credentials);
  return response.data;
};

export const logout = async () => {
  await apiClient.post('/auth/logout');
};

// Products
export const fetchProducts = async () => {
  const response = await apiClient.get('/products');
  return response.data;
};

export const createProduct = async (product) => {
  const response = await apiClient.post('/products', product);
  return response.data;
};

export const updateProduct = async (productId, product) => {
  const response = await apiClient.put(`/products/${productId}`, product);
  return response.data;
};

export const deleteProduct = async (productId) => {
  await apiClient.delete(`/products/${productId}`);
};

// Warehouses
export const fetchWarehouses = async () => {
  const response = await apiClient.get('/warehouses');
  return response.data;
};

export const createWarehouse = async (warehouse) => {
  const response = await apiClient.post('/warehouses', warehouse);
  return response.data;
};

export const updateWarehouse = async (warehouseId, warehouse) => {
  const response = await apiClient.put(`/warehouses/${warehouseId}`, warehouse);
  return response.data;
};

export const deleteWarehouse = async (warehouseId) => {
  await apiClient.delete(`/warehouses/${warehouseId}`);
};