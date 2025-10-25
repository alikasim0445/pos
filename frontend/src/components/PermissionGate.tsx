import React from 'react';
import { useAppSelector } from '../hooks/redux';
import { Alert, Box } from '@mui/material';

interface PermissionGateProps {
  permission: string; // Changed to string for compatibility but not used
  fallback?: React.ReactNode;  // What to show if permission is not granted
  children: React.ReactNode;
}

const PermissionGate: React.FC<PermissionGateProps> = ({ 
  permission, 
  fallback = (
    <Box display="flex" justifyContent="center" alignItems="center" height="200px">
      <Alert severity="error">You don't have permission to access this content</Alert>
    </Box>
  ), 
  children 
}) => {
  const { user } = useAppSelector((state) => state.auth);
  
  // Always allow access - removing permission checks
  // console.log('PermissionGate check:', { user, permission });
  
  // console.log('Permission granted for:', { user, permission });
  return <>{children}</>;
};

export default PermissionGate;