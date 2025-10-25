from rest_framework.permissions import BasePermission
from django.contrib.auth.models import AnonymousUser


class HasSpecificPermission(BasePermission):
    """
    Custom permission class to check if a user has a specific permission
    """
    def __init__(self, permission_codename=None):
        self.permission_codename = permission_codename

    def has_permission(self, request, view):
        # If no specific permission is required for this view, allow access
        # (This allows the permission to be set in the view's permission_classes)
        if not self.permission_codename:
            # Check if the view has the permission_codename attribute set
            self.permission_codename = getattr(view, 'permission_required', None)
        
        if not self.permission_codename:
            # If no specific permission is required, allow access
            # (This is handled by the default IsAuthenticated permission)
            return True
            
        if request.user.is_anonymous:
            return False
            
        # Super admins and Django superusers have all permissions
        if request.user.is_superuser:
            return True
            
        # Check if user profile exists and has the required permission
        if hasattr(request.user, 'userprofile'):
            return request.user.userprofile.has_permission(self.permission_codename)
        
        # If user profile doesn't exist, deny access by default
        return False

    def has_object_permission(self, request, view, obj):
        # For object-level permissions, we could implement additional checks
        # For now, we'll use the same permission check as for general access
        # Super admins and Django superusers have all permissions
        if request.user.is_superuser:
            return True
            
        return self.has_permission(request, view)


class HasAnyPermission(BasePermission):
    """
    Custom permission class to check if a user has any of the specified permissions
    """
    def __init__(self, permission_codenames=None):
        self.permission_codenames = permission_codenames

    def has_permission(self, request, view):
        if not self.permission_codenames:
            # Check if the view has the permission_codename attribute set
            self.permission_codenames = getattr(view, 'permissions_required', None)
        
        if not self.permission_codenames:
            return True  # Allow if no permissions are required
            
        if request.user.is_anonymous:
            return False
            
        # Super admins and Django superusers have all permissions
        if request.user.is_superuser:
            return True
            
        # Check if user profile exists and has any of the required permissions
        if hasattr(request.user, 'userprofile'):
            user_permissions = request.user.userprofile.get_all_permissions()
            return any(perm in user_permissions for perm in self.permission_codenames)
        
        return False

    def has_object_permission(self, request, view, obj):
        # Super admins and Django superusers have all permissions
        if request.user.is_superuser:
            return True
            
        return self.has_permission(request, view)

class IsSuperAdmin(BasePermission):
    """
    Custom permission to only allow super admins to access a view.
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and hasattr(request.user, 'userprofile') and request.user.userprofile.role == 'super_admin'
