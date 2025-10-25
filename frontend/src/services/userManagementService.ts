import axios from 'axios';
import { User } from '../types';

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

export const userManagementService = {
  // Get all users
  getAllUsers: async (): Promise<User[]> => {
    const response = await apiClient.get('/super-admin/users/');
    return response.data;
  },

  // Update user profile and role
  updateUserProfile: async (userId: number, data: Partial<User>): Promise<User> => {
    const response = await apiClient.patch(`/super-admin/users/${userId}/`, data);
    return response.data;
  },

  // Create user with role
  createUserWithRole: async (userData: {
    email: string;
    password: string;
    password_confirm: string;
    first_name: string;
    last_name: string;
    username: string;
    role: string;
  }): Promise<User> => {
    const response = await apiClient.post('/super-admin/users/', userData);
    return response.data;
  },

  // Delete user
  deleteUser: async (userId: number): Promise<void> => {
    await apiClient.delete(`/super-admin/users/${userId}/`);
  },

  // Reset user password
  resetUserPassword: async (userId: number, newPassword: string): Promise<any> => {
    const response = await apiClient.post(`/super-admin/users/${userId}/reset-password/`, {
      new_password: newPassword
    });
    return response.data;
  },

  // Reset user MFA
  resetUserMfa: async (userId: number): Promise<any> => {
    const response = await apiClient.post(`/super-admin/users/${userId}/mfa/reset/`, {});
    return response.data;
  },

  // Get user management dashboard data
  getUserManagementDashboard: async (): Promise<any> => {
    const response = await apiClient.get('/user-management-dashboard/');
    return response.data;
  },
};

