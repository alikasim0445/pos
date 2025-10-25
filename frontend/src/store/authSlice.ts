import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';
import axios from 'axios';
import { User } from '../types';

// Define the base API URL
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';

interface AuthState {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  error: string | null;
  isAuthenticated: boolean;
}

// Initial state
const initialState: AuthState = {
  user: null,
  token: null,
  isLoading: false,
  error: null,
  isAuthenticated: false,
};

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

// Async thunk for login
export const login = createAsyncThunk(
  'auth/login',
  async ({ email, password }: { email: string; password: string }, { rejectWithValue }) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/token/`, {
        username: email, // This can now be either email or username due to backend changes
        password,
      });

      const { access, refresh, user_id, username, email: userEmail } = response.data;
      
      // Set token in localStorage
      localStorage.setItem('token', access);
      localStorage.setItem('refreshToken', refresh);

      // Try to get user details, but handle potential permission issues
      let user;
      try {
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${access}`;
        const userResponse = await apiClient.get(`/users/${user_id}/`);
        user = userResponse.data;
      } catch (userDetailsError) {
        // If user details request fails (possibly due to permissions),
        // create a basic user object with available data
        // Check if this might be a super admin user
        user = {
          id: user_id,
          username: username,
          email: userEmail,
          first_name: '', // Will be updated if needed
          last_name: '',
          date_joined: '',
          profile: {
            role: username === 'lammii' ? 'super_admin' : '', // Special case for lammii user
          },
        };
      }
      
      // Store user in localStorage
      localStorage.setItem('user', JSON.stringify(user));

      return { user, token: access };
    } catch (error: any) {
      if (error.response && error.response.data) {
        return rejectWithValue(error.response.data);
      } else {
        return rejectWithValue(error.message || 'Login failed');
      }
    }
  }
);

// Async thunk for logout
export const logout = createAsyncThunk('auth/logout', async (_, { rejectWithValue }) => {
  try {
    const refreshToken = localStorage.getItem('refreshToken');
    if (refreshToken) {
      await apiClient.post('/logout/', { refresh: refreshToken });
    }
  } catch (error: any) {
    // Even if blacklisting fails, proceed with client-side logout
    console.error('Failed to blacklist token on server', error);
  } finally {
    // Clear user and tokens from localStorage
    localStorage.removeItem('user');
    localStorage.removeItem('token');
    localStorage.removeItem('refreshToken');
  }
});

// Async thunk for register
export const register = createAsyncThunk(
  'auth/register',
  async (
    { email, password, password_confirm, firstName, lastName, username, role = 'cashier' }: { 
      email: string; 
      password: string; 
      password_confirm: string;
      firstName: string; 
      lastName: string;
      username: string;
      role?: string;
    },
    { rejectWithValue }
  ) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/register/`, {
        email,
        password,
        password_confirm,
        first_name: firstName,
        last_name: lastName,
        username,
        role,
      });

      // Login immediately after registration using the provided username
      const loginResponse = await axios.post(`${API_BASE_URL}/token/`, {
        username: username,
        password,
      });

      const { access, refresh, user_id, username: returnedUsername, email: returnedEmail } = loginResponse.data;
      
      // Set token in localStorage
      localStorage.setItem('token', access);
      localStorage.setItem('refreshToken', refresh);

      // Set token in localStorage
      localStorage.setItem('token', access);

      // Try to get user details, but handle potential permission issues
      let user;
      try {
        apiClient.defaults.headers.common['Authorization'] = `Bearer ${access}`;
        const userResponse = await apiClient.get(`/users/${user_id}/`);
        user = userResponse.data;
      } catch (userDetailsError) {
        // If user details request fails (possibly due to permissions),
        // create a basic user object with available data
        user = {
          id: user_id,
          username: returnedUsername,
          email: returnedEmail,
          first_name: firstName,
          last_name: lastName,
          date_joined: new Date().toISOString(),
          profile: {
            role: role,
          },
        };
      }
      
      // Store user in localStorage
      localStorage.setItem('user', JSON.stringify(user));

      return { user, token: access };
    } catch (error: any) {
      if (error.response && error.response.data) {
        return rejectWithValue(error.response.data);
      } else {
        return rejectWithValue(error.message || 'Registration failed');
      }
    }
  }
);

// Async thunk for password reset request
export const passwordResetRequest = createAsyncThunk(
  'auth/passwordResetRequest',
  async (email: string, { rejectWithValue }) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/password-reset/`, {
        email,
      });
      return response.data;
    } catch (error: any) {
      if (error.response && error.response.data) {
        return rejectWithValue(error.response.data);
      } else {
        return rejectWithValue(error.message || 'Password reset request failed');
      }
    }
  }
);

// Async thunk for password reset confirm
export const passwordResetConfirm = createAsyncThunk(
  'auth/passwordResetConfirm',
  async ({ uidb64, token, new_password, confirm_password }: { 
    uidb64: string; 
    token: string; 
    new_password: string; 
    confirm_password: string; 
  }, { rejectWithValue }) => {
    try {
      const response = await axios.post(`${API_BASE_URL}/password-reset-confirm/${uidb64}/${token}/`, {
        new_password,
        confirm_password,
      });
      return response.data;
    } catch (error: any) {
      if (error.response && error.response.data) {
        return rejectWithValue(error.response.data);
      } else {
        return rejectWithValue(error.message || 'Password reset confirmation failed');
      }
    }
  }
);

const authSlice = createSlice({
  name: 'auth',
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null;
    },
    restoreAuthState: (state) => {
      const token = localStorage.getItem('token');
      const refreshToken = localStorage.getItem('refreshToken');
      
      if (token && refreshToken) {
        state.token = token;
        state.isAuthenticated = true;
        
        // Try to get user info from the token
        // In a real app, you'd decode the token or make an API call to get user info
        try {
          const userStr = localStorage.getItem('user');
          if (userStr) {
            state.user = JSON.parse(userStr);
          }
        } catch (e) {
          console.error('Error parsing user from localStorage', e);
        }
      }
    },
    updateUserInStore: (state, action: PayloadAction<User>) => {
      state.user = action.payload;
      // Update the user in localStorage as well
      localStorage.setItem('user', JSON.stringify(action.payload));
    },
  },
  extraReducers: (builder) => {
    builder
      // Login cases
      .addCase(login.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(login.fulfilled, (state, action: PayloadAction<{ user: User; token: string }>) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(login.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        state.isAuthenticated = false;
      })
      // Logout cases
      .addCase(logout.fulfilled, (state) => {
        state.user = null;
        state.token = null;
        state.isAuthenticated = false;
        state.error = null;
      })
      // Register cases
      .addCase(register.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(register.fulfilled, (state, action: PayloadAction<{ user: User; token: string }>) => {
        state.isLoading = false;
        state.user = action.payload.user;
        state.token = action.payload.token;
        state.isAuthenticated = true;
        state.error = null;
      })
      .addCase(register.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
        state.isAuthenticated = false;
      })
      // Password reset request cases
      .addCase(passwordResetRequest.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(passwordResetRequest.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(passwordResetRequest.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      })
      // Password reset confirm cases
      .addCase(passwordResetConfirm.pending, (state) => {
        state.isLoading = true;
        state.error = null;
      })
      .addCase(passwordResetConfirm.fulfilled, (state) => {
        state.isLoading = false;
        state.error = null;
      })
      .addCase(passwordResetConfirm.rejected, (state, action) => {
        state.isLoading = false;
        state.error = action.payload as string;
      });
  },
});

export const { clearError, restoreAuthState, updateUserInStore } = authSlice.actions;
export default authSlice.reducer;