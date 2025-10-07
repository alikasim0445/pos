import React from 'react';
import { useAppSelector } from '../hooks/redux';
import { Navigate, useLocation } from 'react-router-dom';

const SuperAdminRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const location = useLocation();

  if (!isAuthenticated || !user) {
    // Redirect to login page and save the attempted route
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if user is a Super Admin
  if (user.profile?.role !== 'super_admin') {
    // Redirect to dashboard if not a super admin
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default SuperAdminRoute;