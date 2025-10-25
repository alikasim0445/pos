import axios from 'axios';

// Define the base API URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

// Create an axios instance with default config
const apiClient = axios.create({
  baseURL: API_BASE_URL,
});

// Add a request interceptor to include the token in all requests
apiClient.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Add a response interceptor to handle token refresh
apiClient.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      // Attempt to refresh the token
      const refreshToken = localStorage.getItem('refreshToken');
      if (refreshToken) {
        try {
          const response = await axios.post(`${API_BASE_URL}/token/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          localStorage.setItem('token', access);
          
          // Retry the original request with the new token
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return axios(originalRequest);
        } catch (refreshError) {
          // If refresh fails, redirect to login
          localStorage.removeItem('token');
          localStorage.removeItem('refreshToken');
          window.location.href = '/login';
          return Promise.reject(refreshError);
        }
      } else {
        // No refresh token, redirect to login
        window.location.href = '/login';
      }
    }
    
    return Promise.reject(error);
  }
);

// Authentication API calls
export const authAPI = {
  login: (email: string, password: string) => 
    axios.post(`${API_BASE_URL}/token/`, { username: email, password }),
  
  register: (email: string, password: string, firstName: string, lastName: string) => 
    axios.post(`${API_BASE_URL}/register/`, { 
      email, 
      password, 
      first_name: firstName, 
      last_name: lastName,
      username: email // Using email as username
    }),
  
  passwordResetRequest: (email: string) =>
    axios.post(`${API_BASE_URL}/password-reset/`, { email }),
  
  passwordResetConfirm: (uidb64: string, token: string, newPassword: string, confirmPassword: string) =>
    axios.post(`${API_BASE_URL}/password-reset-confirm/${uidb64}/${token}/`, {
      new_password: newPassword,
      confirm_password: confirmPassword
    }),
  
  logout: () => {
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
    localStorage.removeItem('user');
  },
};

// User API calls
export const userAPI = {
  getCurrentUser: () => apiClient.get('/users/'),
  getUserById: (id: number) => apiClient.get(`/users/${id}/`),
  updateUser: (id: number, userData: any) => apiClient.put(`/users/${id}/`, userData),
  deleteUser: (id: number) => apiClient.delete(`/users/${id}/`),
  
  // Transfer API calls
  getAllTransfers: () => apiClient.get('/transfers/'),
  updateTransfer: (id: number, transferData: any) => apiClient.put(`/transfers/${id}/`, transferData),
};

// 
export const productAPI = {
  getProducts: () => apiClient.get('/products/'),
  getProductById: (id: number) => apiClient.get(`/products/${id}/`),
  createProduct: (productData: FormData) => apiClient.post('/products/', productData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }),
  updateProduct: (id: number, productData: FormData) => apiClient.patch(`/products/${id}/`, productData, {
    headers: {
      'Content-Type': 'multipart/form-data'
    }
  }),
  deleteProduct: (id: number) => apiClient.delete(`/products/${id}/`),
};

// Warehouse API calls
export const warehouseAPI = {
  getWarehouses: () => apiClient.get('/warehouses/'),
  getWarehouseById: (id: number) => apiClient.get(`/warehouses/${id}/`),
  createWarehouse: (warehouseData: any) => apiClient.post('/warehouses/', warehouseData),
  updateWarehouse: (id: number, warehouseData: any) => apiClient.put(`/warehouses/${id}/`, warehouseData),
  deleteWarehouse: (id: number) => apiClient.delete(`/warehouses/${id}/`),
};

// Inventory API calls
export const inventoryAPI = {
  getInventory: () => apiClient.get('/inventory/'),
  getInventoryById: (id: number) => apiClient.get(`/inventory/${id}/`),
  createInventory: (inventoryData: any) => apiClient.post('/inventory/', inventoryData),
  updateInventory: (id: number, inventoryData: any) => apiClient.put(`/inventory/${id}/`, inventoryData),
  deleteInventory: (id: number) => apiClient.delete(`/inventory/${id}/`),
  getLowStockAlerts: () => apiClient.get('/inventory/low_stock/'),
};

// Category API calls
export const categoryAPI = {
  getCategories: () => apiClient.get('/categories/'),
  getCategoryById: (id: number) => apiClient.get(`/categories/${id}/`),
  createCategory: (categoryData: any) => apiClient.post('/categories/', categoryData),
  updateCategory: (id: number, categoryData: any) => apiClient.put(`/categories/${id}/`, categoryData),
  deleteCategory: (id: number) => apiClient.delete(`/categories/${id}/`),
};

// Customer API calls
export const customerAPI = {
  getCustomers: () => apiClient.get('/customers/'),
  getCustomerById: (id: number) => apiClient.get(`/customers/${id}/`),
  getCustomerPurchaseHistory: (id: number) => apiClient.get(`/customers/${id}/purchase-history/`),
  createCustomer: (customerData: any) => apiClient.post('/customers/', customerData),
  updateCustomer: (id: number, customerData: any) => apiClient.put(`/customers/${id}/`, customerData),
  deleteCustomer: (id: number) => apiClient.delete(`/customers/${id}/`),
};

// Sale API calls
export const saleAPI = {
  getSales: () => apiClient.get('/sales/'),
  getSaleById: (id: number) => apiClient.get(`/sales/${id}/`),
  createSale: (saleData: any) => apiClient.post('/sales/create/', saleData),
  updateSale: (id: number, saleData: any) => apiClient.put(`/sales/${id}/`, saleData),
  deleteSale: (id: number) => apiClient.delete(`/sales/${id}/`),
  downloadReceipt: (saleId: number) => {
    return apiClient.get(`/sales/${saleId}/receipt/`, {
      responseType: 'blob', // Important: set response type to blob for PDF
    });
  },
};

export const reservationAPI = {
  getReservations: () => apiClient.get('/reservations/'),
  getReservationById: (id: number) => apiClient.get(`/reservations/${id}/`),
  createReservation: (data: any) => apiClient.post('/reservations/', data),
  updateReservation: (id: number, data: any) => apiClient.put(`/reservations/${id}/`, data),
  deleteReservation: (id: number) => apiClient.delete(`/reservations/${id}/`),
};

// Transfer API calls
export const transferAPI = {
  getTransfers: () => apiClient.get('/transfers/'),
  getTransferById: (id: number) => apiClient.get(`/transfers/${id}/`),
  createTransfer: (transferData: any) => apiClient.post('/transfers/', transferData),
  updateTransfer: (id: number, transferData: any) => apiClient.put(`/transfers/${id}/`, transferData),
  deleteTransfer: (id: number) => apiClient.delete(`/transfers/${id}/`),
};

// Return API calls
export const returnAPI = {
  getReturns: () => apiClient.get('/returns/'),
  getReturnById: (id: number) => apiClient.get(`/returns/${id}/`),
  createReturn: (returnData: any) => apiClient.post('/returns/', returnData),
  updateReturn: (id: number, returnData: any) => apiClient.put(`/returns/${id}/`, returnData),
  deleteReturn: (id: number) => apiClient.delete(`/returns/${id}/`),
};

// Report API calls
export const reportAPI = {
  getSalesReport: (params?: any) => apiClient.get('/reports/sales/', { params }),
  getInventoryReport: (params?: any) => apiClient.get('/reports/inventory/', { params }),
  getProfitabilityReport: (params?: any) => apiClient.get('/reports/profitability/', { params }),
  getTransferReport: (params?: any) => apiClient.get('/reports/transfers/', { params }),
};

// Purchase Order & Receiving API calls
export const purchaseOrderAPI = {
  getPurchaseOrders: () => apiClient.get('/purchase-orders/'),
  getPurchaseOrderById: (id: number) => apiClient.get(`/purchase-orders/${id}/`),
  createPurchaseOrder: (poData: any) => apiClient.post('/purchase-orders/', poData),
  updatePurchaseOrder: (id: number, poData: any) => apiClient.put(`/purchase-orders/${id}/`, poData),
  deletePurchaseOrder: (id: number) => apiClient.delete(`/purchase-orders/${id}/`),
};

export const grnAPI = {
  getGRNs: () => apiClient.get('/grns/'),
  getGRNById: (id: number) => apiClient.get(`/grns/${id}/`),
  createGRN: (grnData: any) => apiClient.post('/grns/', grnData),
  updateGRN: (id: number, grnData: any) => apiClient.put(`/grns/${id}/`, grnData),
  deleteGRN: (id: number) => apiClient.delete(`/grns/${id}/`),
};

// Promotion/Discount API calls
export const promotionAPI = {
  getPromotions: () => apiClient.get('/promotions/'),
  getPromotionById: (id: number) => apiClient.get(`/promotions/${id}/`),
  createPromotion: (promotionData: any) => apiClient.post('/promotions/', promotionData),
  updatePromotion: (id: number, promotionData: any) => apiClient.put(`/promotions/${id}/`, promotionData),
  deletePromotion: (id: number) => apiClient.delete(`/promotions/${id}/`),
};

export const couponAPI = {
  getCoupons: () => apiClient.get('/coupons/'),
  getCouponById: (id: number) => apiClient.get(`/coupons/${id}/`),
  createCoupon: (couponData: any) => apiClient.post('/coupons/', couponData),
  updateCoupon: (id: number, couponData: any) => apiClient.put(`/coupons/${id}/`, couponData),
  deleteCoupon: (id: number) => apiClient.delete(`/coupons/${id}/`),
  verifyCoupon: (code: string) => apiClient.get(`/coupons/verify/${code}/`),
};

// Location API calls
export const locationAPI = {
  getLocations: () => apiClient.get('/locations/'),
  getLocationById: (id: number) => apiClient.get(`/locations/${id}/`),
  getLocationsByWarehouse: (warehouseId: string) => apiClient.get(`/locations/?warehouse=${warehouseId}`),
  createLocation: (locationData: any) => apiClient.post('/locations/', locationData),
  updateLocation: (id: number, locationData: any) => apiClient.put(`/locations/${id}/`, locationData),
  deleteLocation: (id: number) => apiClient.delete(`/locations/${id}/`),
};

// Bin API calls
export const binAPI = {
  getBins: () => apiClient.get('/bins/'),
  getBinById: (id: number) => apiClient.get(`/bins/${id}/`),
  getBinsByLocation: (locationId: string) => apiClient.get(`/bins/?location=${locationId}`),
  createBin: (binData: any) => apiClient.post('/bins/', binData),
  updateBin: (id: number, binData: any) => apiClient.put(`/bins/${id}/`, binData),
  deleteBin: (id: number) => apiClient.delete(`/bins/${id}/`),
};

export default apiClient;