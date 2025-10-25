#!/usr/bin/env python
"""
RBAC System Demonstration Script
===============================

This script demonstrates the new Role-Based Access Control (RBAC) system
with permission groups that was implemented for the POS Management System.

The system includes:
1. Role-based permissions (backward compatibility)
2. Individual permissions (fine-grained control)
3. Permission groups (collections of related permissions)
4. Flexible assignment of permissions to roles and users
"""

import os
import sys

# Setup Django environment BEFORE importing Django modules
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pos_project.settings')

# Now we can import Django modules
import django
django.setup()

from django.contrib.auth.models import User
from django.db import transaction
from pos_app.models import UserProfile, Permission, PermissionGroup

def demonstrate_rbac_system():
    """Demonstrate the new RBAC system features"""
    
    print("=" * 60)
    print("POS Management System - RBAC System Demonstration")
    print("=" * 60)
    
    # Create sample permissions
    print("\n1. Creating Sample Permissions...")
    permissions_data = [
        ('add_product', 'Can add products', 'Add Product'),
        ('change_product', 'Can change products', 'Change Product'),
        ('delete_product', 'Can delete products', 'Delete Product'),
        ('view_product', 'Can view products', 'View Product'),
        ('add_sale', 'Can add sales', 'Add Sale'),
        ('change_sale', 'Can change sales', 'Change Sale'),
        ('delete_sale', 'Can delete sales', 'Delete Sale'),
        ('view_sale', 'Can view sales', 'View Sale'),
        ('add_user', 'Can add users', 'Add User'),
        ('change_user', 'Can change users', 'Change User'),
        ('delete_user', 'Can delete users', 'Delete User'),
        ('view_user', 'Can view users', 'View User'),
        ('view_inventory', 'Can view inventory', 'View Inventory'),
        ('change_inventory', 'Can change inventory', 'Change Inventory'),
        ('view_sales_report', 'Can view sales reports', 'View Sales Report'),
        ('view_inventory_report', 'Can view inventory reports', 'View Inventory Report'),
        ('view_profitability_report', 'Can view profitability reports', 'View Profitability Report'),
    ]
    
    created_permissions = []
    for codename, description, name in permissions_data:
        permission, created = Permission.objects.get_or_create(
            codename=codename,
            defaults={'name': name, 'description': description}
        )
        created_permissions.append(permission)
        status = "CREATED" if created else "EXISTS"
        print(f"   - {name} ({codename}) [{status}]")
    
    # Create permission groups
    print("\n2. Creating Permission Groups...")
    groups_data = [
        ('Sales Management', 'Permissions for managing sales operations', 
         ['add_sale', 'change_sale', 'delete_sale', 'view_sale']),
        ('Product Management', 'Permissions for managing products',
         ['add_product', 'change_product', 'delete_product', 'view_product']),
        ('User Management', 'Permissions for managing users',
         ['add_user', 'change_user', 'delete_user', 'view_user']),
        ('Inventory Management', 'Permissions for managing inventory',
         ['view_inventory', 'change_inventory']),
        ('Reporting', 'Permissions for viewing reports',
         ['view_sales_report', 'view_inventory_report', 'view_profitability_report']),
    ]
    
    created_groups = []
    for name, description, perm_codenames in groups_data:
        group, created = PermissionGroup.objects.get_or_create(
            name=name,
            defaults={'description': description}
        )
        
        # Add permissions to group
        perms = Permission.objects.filter(codename__in=perm_codenames)
        group.permissions.set(perms)
        group.save()
        
        created_groups.append(group)
        status = "CREATED" if created else "EXISTS"
        print(f"   - {name} [{status}] - {perms.count()} permissions")
    
    # Create sample users with different roles
    print("\n3. Creating Sample Users...")
    users_data = [
        ('admin_user', 'admin@example.com', 'Admin', 'User', 'admin'),
        ('store_manager_user', 'manager@example.com', 'Store', 'Manager', 'store_manager'),
        ('cashier_user', 'cashier@example.com', 'Cashier', 'User', 'cashier'),
        ('accountant_user', 'accountant@example.com', 'Accountant', 'User', 'accountant'),
    ]
    
    created_users = []
    for username, email, first_name, last_name, role in users_data:
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                'email': email,
                'first_name': first_name,
                'last_name': last_name,
            }
        )
        
        if created:
            user.set_password('testpass123')
            user.save()
        
        # Get or create user profile
        profile, _ = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': role}
        )
        
        # Assign additional permission groups based on role
        if role == 'admin':
            # Admin gets all groups
            profile.permission_groups.set(created_groups)
        elif role == 'store_manager':
            # Store manager gets sales and product management
            sales_group = PermissionGroup.objects.get(name='Sales Management')
            product_group = PermissionGroup.objects.get(name='Product Management')
            profile.permission_groups.set([sales_group, product_group])
        elif role == 'accountant':
            # Accountant gets reporting permissions
            reporting_group = PermissionGroup.objects.get(name='Reporting')
            profile.permission_groups.add(reporting_group)
        
        profile.save()
        created_users.append((user, profile))
        
        status = "CREATED" if created else "EXISTS"
        print(f"   - {first_name} {last_name} ({username}) - Role: {role} [{status}]")
    
    # Demonstrate permission checking
    print("\n4. Demonstrating Permission Checks...")
    test_cases = [
        ('admin_user', 'add_product', 'Admin should be able to add products'),
        ('admin_user', 'add_user', 'Admin should be able to add users'),
        ('cashier_user', 'add_sale', 'Cashier should be able to add sales'),
        ('cashier_user', 'add_product', 'Cashier should NOT be able to add products'),
        ('accountant_user', 'view_sales_report', 'Accountant should be able to view sales reports'),
        ('accountant_user', 'add_product', 'Accountant should NOT be able to add products'),
        ('store_manager_user', 'add_sale', 'Store manager should be able to add sales'),
        ('store_manager_user', 'add_user', 'Store manager should NOT be able to add users'),
    ]
    
    for username, permission_codename, description in test_cases:
        try:
            user = User.objects.get(username=username)
            profile = user.userprofile
            has_perm = profile.has_permission(permission_codename)
            result = "✓ PASS" if has_perm else "✗ FAIL"
            print(f"   {result}: {description}")
        except User.DoesNotExist:
            print(f"   ERROR: User {username} not found")
    
    # Show user permissions
    print("\n5. User Permissions Summary:")
    for user, profile in created_users:
        print(f"\n   {user.first_name} {user.last_name} ({profile.role}):")
        permissions = profile.get_all_permissions()
        print(f"      Total permissions: {len(permissions)}")
        # Show first 10 permissions
        for perm in sorted(list(permissions)[:10]):
            print(f"         - {perm}")
        if len(permissions) > 10:
            print(f"         ... and {len(permissions) - 10} more")
    
    print("\n" + "=" * 60)
    print("RBAC System Demonstration Complete!")
    print("=" * 60)
    print("\nKey Features Demonstrated:")
    print("• Role-based permissions (backward compatible)")
    print("• Fine-grained individual permissions")
    print("• Permission groups for easier management")
    print("• Flexible assignment of permissions to roles/users")
    print("• Dynamic permission checking")

if __name__ == '__main__':
    demonstrate_rbac_system()