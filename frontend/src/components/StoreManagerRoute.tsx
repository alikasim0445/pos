import React from 'react';
import { useAppSelector } from '../hooks/redux';
import { Navigate, useLocation } from 'react-router-dom';
import { hasRoleLevel } from '../utils/roleUtils';

const StoreManagerRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, user } = useAppSelector((state) => state.auth);
  const location = useLocation();

  if (!isAuthenticated || !user) {
    // Redirect to login page and save the attempted route
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Check if user has store manager or higher role
  if (!hasRoleLevel(user, 'store_manager')) {
    // Redirect to dashboard if not authorized
    return <Navigate to="/" replace />;
  }

  return <>{children}</>;
};

export default StoreManagerRoute;