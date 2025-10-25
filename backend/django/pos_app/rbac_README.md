# POS Management System - RBAC System Documentation

## Overview

This document describes the enhanced Role-Based Access Control (RBAC) system implemented for the POS Management System. The system extends the existing role-based approach with a more flexible permission model that includes individual permissions, permission groups, and fine-grained access control.

## Key Features

### 1. Role-Based Permissions (Backward Compatible)
The system maintains backward compatibility with the existing role-based approach:
- Super Admin: Full system access
- Admin: Administrative access to most features
- Store Manager: Store operations access
- Warehouse Manager: Inventory management access
- Cashier: Basic sales operations access
- Accountant: Financial reporting access

### 2. Individual Permissions
Each user can have specific permissions assigned independently:
```python
# Check if user has specific permission
if user.userprofile.has_permission('add_product'):
    # Allow product creation
```

### 3. Permission Groups
Collections of related permissions that can be assigned together:
- Sales Management: Add/Edit/Delete/View sales
- Product Management: Add/Edit/Delete/View products
- User Management: Add/Edit/Delete/View users
- Inventory Management: View/Modify inventory
- Reporting: Access various reports

### 4. Flexible Assignment
Permissions can be assigned at multiple levels:
- Role-based (default permissions for each role)
- Group-based (collections of permissions assigned to roles/users)
- Individual-based (specific permissions for specific users)

## Implementation Details

### Backend Models

1. **Permission Model**
   - Represents individual permissions
   - Fields: name, description, codename
   - Example: 'add_product', 'view_sales_report'

2. **PermissionGroup Model**
   - Collection of related permissions
   - Fields: name, description, permissions (ManyToMany)
   - Example: 'Sales Management' group with add_sale, change_sale, etc.

3. **UserProfile Model Enhancement**
   - Added permission_groups field (ManyToMany to PermissionGroup)
   - Added get_all_permissions() method
   - Added has_permission() method

### Frontend Components

1. **PermissionGate Component**
   - React component to conditionally render content based on permissions
   ```jsx
   <PermissionGate permission="add_product">
       <AddProductButton />
   </PermissionGate>
   ```

2. **Role Utilities**
   - Enhanced hasPermission() function
   - Support for checking individual or grouped permissions
   - Fallback to role-based permissions for backward compatibility

3. **Navigation Filtering**
   - Menu items filtered based on user permissions
   - Dynamic UI elements shown/hidden based on permissions

## Usage Examples

### Backend Permission Check
```python
# In a view
if not request.user.userprofile.has_permission('add_product'):
    raise PermissionDenied("You don't have permission to add products")
```

### Frontend Permission Check
```jsx
// Conditional rendering
{hasPermission(user, 'add_product') && (
    <AddProductButton />
)}

// Using PermissionGate component
<PermissionGate permission="add_product">
    <ProductForm />
</PermissionGate>
```

## Testing

The system includes comprehensive testing for:
- Permission inheritance from roles
- Permission assignment via groups
- Individual permission overrides
- UI filtering based on permissions
- API access control

## Migration

The new system is fully backward compatible. Existing role-based access continues to work unchanged while providing the option to use the enhanced permission model.

## Benefits

1. **Granular Control**: More precise access control than simple roles
2. **Flexibility**: Easy to customize permissions for specific users or roles
3. **Maintainability**: Permission groups make it easy to manage collections of permissions
4. **Scalability**: Simple to add new permissions as system grows
5. **Compatibility**: Works with existing role-based system

## Future Enhancements

1. **Object-Level Permissions**: Per-record access control
2. **Time-Based Permissions**: Permissions that expire or become active at specific times
3. **Permission Auditing**: Track permission changes and usage
4. **Dynamic Permission Creation**: Admin interface for creating new permissions/groups