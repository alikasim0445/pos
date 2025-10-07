import React, { useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useDispatch } from 'react-redux';
import { restoreAuthState } from './store/authSlice';
import Dashboard from './pages/Dashboard';
import Sales from './pages/Sales';
import Products from './pages/Products';
import Warehouses from './pages/Warehouses';
import Customers from './pages/Customers';
import Reports from './pages/Reports';
import Promotions from './pages/Promotions';
import PurchaseOrders from './pages/PurchaseOrders';
import Profile from './pages/Profile';
import Users from './pages/Users';
import Login from './components/Login';
import Register from './components/Register';
import ForgotPassword from './components/ForgotPassword';
import ResetPassword from './components/ResetPassword';
import AppLayout from './components/AppLayout';
import ProtectedRoute from './components/ProtectedRoute';
import SuperAdminRoute from './components/SuperAdminRoute';

const App: React.FC = () => {
  const dispatch = useDispatch();

  useEffect(() => {
    // Restore authentication state on app load
    dispatch(restoreAuthState());
  }, [dispatch]);

  return (
    <Router>
      <Routes>
        {/* Public routes */}
        <Route path="/login" element={<Login />} />
        <Route path="/register" element={<Register />} />
        <Route path="/forgot-password" element={<ForgotPassword />} />
        <Route path="/reset-password/:uidb64/:token/" element={<ResetPassword />} />
        
        {/* Protected routes with layout */}
        <Route 
          path="/" 
          element={
            
              <AppLayout>
                <Dashboard />
              </AppLayout>
            
          } 
        />
        <Route 
          path="/sales" 
          element={
            
              <AppLayout>
                <Sales />
              </AppLayout>
            
          } 
        />
        <Route 
          path="/products" 
          element={
            
              <AppLayout>
                <Products />
              </AppLayout>
           
          } 
        />
        <Route 
          path="/warehouses" 
          element={
            <ProtectedRoute>
              <AppLayout>
                <Warehouses />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/customers" 
          element={
            <ProtectedRoute>
              <AppLayout>
                <Customers />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/reports" 
          element={
            <ProtectedRoute>
              <AppLayout>
                <Reports />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/promotions" 
          element={
            <ProtectedRoute>
              <AppLayout>
                <Promotions />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/purchase-orders" 
          element={
            <ProtectedRoute>
              <AppLayout>
                <PurchaseOrders />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/profile" 
          element={
            <ProtectedRoute>
              <AppLayout>
                <Profile />
              </AppLayout>
            </ProtectedRoute>
          } 
        />
        <Route 
          path="/users" 
          element={
            
              <AppLayout>
                <Users />
              </AppLayout>
            
          } 
        />
        
        {/* Redirect any unmatched routes to dashboard if authenticated, otherwise to login */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
};

export default App;