import { User } from '../types';
import { ROLES, ROLE_HIERARCHY, ROLE_PERMISSIONS, Permission, Role } from '../constants/roles';

// Check if user has a specific role
export const hasRole = (user: User | null, requiredRole: Role): boolean => {
  if (!user || !user.profile) return false;
  return user.profile.role === requiredRole;
};

// Check if user has any of the required roles
export const hasAnyRole = (user: User | null, requiredRoles: Role[]): boolean => {
  if (!user || !user.profile) return false;
  return requiredRoles.includes(user.profile.role as Role);
};

// Check if current user's role is equal or higher than required role
export const hasRoleLevel = (user: User | null, requiredRole: Role): boolean => {
  if (!user || !user.profile) return false;
  const userRoleLevel = ROLE_HIERARCHY[user.profile.role as Role] || 0;
  const requiredRoleLevel = ROLE_HIERARCHY[requiredRole] || 0;
  return userRoleLevel >= requiredRoleLevel;
};

// Check if user is a Super Admin
export const isSuperAdmin = (user: User | null): boolean => {
  if (!user || !user.profile) return false;
  return user.profile.role === ROLES.SUPER_ADMIN;
};

// Check permissions based on role and action
export const hasPermission = (user: User | null, permission: Permission): boolean => {
  if (!user || !user.profile) return false;

  // Super admins have access to everything
  if (isSuperAdmin(user)) {
    return true;
  }

  // For all other authenticated users, allow access to all permissions (removing granular restrictions)
  // This maintains basic authentication while removing specific permission checks
  return true;
};

// Check if user has any of the provided permissions
export const hasAnyPermission = (user: User | null, permissions: Permission[]): boolean => {
  if (!user || !permissions || permissions.length === 0) return false;

  return permissions.some(permission => hasPermission(user, permission));
};

// Check if user has all of the provided permissions
export const hasAllPermissions = (user: User | null, permissions: Permission[]): boolean => {
  if (!user || !permissions || permissions.length === 0) return false;

  return permissions.every(permission => hasPermission(user, permission));
};
