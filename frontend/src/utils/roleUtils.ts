import { User } from '../types';

// Define role hierarchy (higher roles can do everything lower roles can do)
export const roleHierarchy = {
  'super_admin': 6,
  'admin': 5,
  'store_manager': 4,
  'warehouse_manager': 3,
  'accountant': 2,
  'cashier': 1,
};

// Check if user has a specific role
export const hasRole = (user: User | null, requiredRole: string): boolean => {
  if (!user || !user.profile) return false;
  return user.profile.role === requiredRole;
};

// Check if user has any of the required roles
export const hasAnyRole = (user: User | null, requiredRoles: string[]): boolean => {
  if (!user || !user.profile) return false;
  return requiredRoles.includes(user.profile.role);
};

// Check if current user's role is equal or higher than required role
export const hasRoleLevel = (user: User | null, requiredRole: string): boolean => {
  if (!user || !user.profile) return false;
  const userRoleLevel = roleHierarchy[user.profile.role] || 0;
  const requiredRoleLevel = roleHierarchy[requiredRole] || 0;
  return userRoleLevel >= requiredRoleLevel;
};

// Check if user is a Super Admin
export const isSuperAdmin = (user: User | null): boolean => {
  return hasRole(user, 'super_admin');
};

// Check permissions based on role and action
export const hasPermission = (user: User | null, permission: string): boolean => {
  if (!user || !user.profile) return false;
  
  const role = user.profile.role;
  
  // Define permissions by role
  const permissions: Record<string, string[]> = {
    'super_admin': [
      'create_user', 'edit_user', 'delete_user', 
      'view_all_reports', 'manage_inventory', 
      'process_returns', 'manage_settings', 'export_data',
      'manage_profiles', 'assign_roles', 'view_user_activity',
      'reset_passwords', 'activate_deactivate_users'
    ],
    'admin': [
      'create_user', 'edit_user', 
      'view_all_reports', 'manage_inventory', 
      'process_returns', 'manage_settings'
    ],
    'store_manager': [
      'view_sales', 'process_sales', 'view_inventory', 
      'manage_customers', 'process_returns', 'view_reports'
    ],
    'warehouse_manager': [
      'view_inventory', 'manage_inventory', 'process_transfers',
      'view_warehouse_reports'
    ],
    'cashier': [
      'process_sales', 'view_products', 'process_payments'
    ],
    'accountant': [
      'view_financial_reports', 'manage_payments', 'view_sales'
    ]
  };
  
  return permissions[role]?.includes(permission) || false;
};