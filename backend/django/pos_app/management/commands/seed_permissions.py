from django.core.management.base import BaseCommand
from django.db import transaction
from pos_app.models import Permission, PermissionGroup

class Command(BaseCommand):
    help = 'Seed the database with initial permissions and permission groups'

    def handle(self, *args, **options):
        self.stdout.write('Seeding permissions and permission groups...')
        
        # Define all permissions
        permissions_data = [
            # User management
            ('add_user', 'Can add users', 'Add User'),
            ('change_user', 'Can change users', 'Change User'),
            ('delete_user', 'Can delete users', 'Delete User'),
            ('view_user', 'Can view users', 'View User'),
            
            # Product management
            ('add_product', 'Can add products', 'Add Product'),
            ('change_product', 'Can change products', 'Change Product'),
            ('delete_product', 'Can delete products', 'Delete Product'),
            ('view_product', 'Can view products', 'View Product'),
            
            # Product variant management
            ('add_productvariant', 'Can add product variants', 'Add Product Variant'),
            ('change_productvariant', 'Can change product variants', 'Change Product Variant'),
            ('delete_productvariant', 'Can delete product variants', 'Delete Product Variant'),
            ('view_productvariant', 'Can view product variants', 'View Product Variant'),
            
            # Category management
            ('add_category', 'Can add categories', 'Add Category'),
            ('change_category', 'Can change categories', 'Change Category'),
            ('delete_category', 'Can delete categories', 'Delete Category'),
            ('view_category', 'Can view categories', 'View Category'),
            
            # Warehouse management
            ('add_warehouse', 'Can add warehouses', 'Add Warehouse'),
            ('change_warehouse', 'Can change warehouses', 'Change Warehouse'),
            ('delete_warehouse', 'Can delete warehouses', 'Delete Warehouse'),
            ('view_warehouse', 'Can view warehouses', 'View Warehouse'),
            
            # Inventory management
            ('add_inventory', 'Can add inventory items', 'Add Inventory'),
            ('change_inventory', 'Can change inventory items', 'Change Inventory'),
            ('delete_inventory', 'Can delete inventory items', 'Delete Inventory'),
            ('view_inventory', 'Can view inventory items', 'View Inventory'),
            
            # Customer management
            ('add_customer', 'Can add customers', 'Add Customer'),
            ('change_customer', 'Can change customers', 'Change Customer'),
            ('delete_customer', 'Can delete customers', 'Delete Customer'),
            ('view_customer', 'Can view customers', 'View Customer'),
            
            # Sale management
            ('add_sale', 'Can add sales', 'Add Sale'),
            ('change_sale', 'Can change sales', 'Change Sale'),
            ('delete_sale', 'Can delete sales', 'Delete Sale'),
            ('view_sale', 'Can view sales', 'View Sale'),
            
            # Sale line management
            ('add_saleline', 'Can add sale lines', 'Add Sale Line'),
            ('change_saleline', 'Can change sale lines', 'Change Sale Line'),
            ('delete_saleline', 'Can delete sale lines', 'Delete Sale Line'),
            ('view_saleline', 'Can view sale lines', 'View Sale Line'),
            
            # Payment management
            ('add_payment', 'Can add payments', 'Add Payment'),
            ('change_payment', 'Can change payments', 'Change Payment'),
            ('delete_payment', 'Can delete payments', 'Delete Payment'),
            ('view_payment', 'Can view payments', 'View Payment'),
            
            # Transfer management
            ('add_transfer', 'Can add transfers', 'Add Transfer'),
            ('change_transfer', 'Can change transfers', 'Change Transfer'),
            ('delete_transfer', 'Can delete transfers', 'Delete Transfer'),
            ('view_transfer', 'Can view transfers', 'View Transfer'),
            
            # Transfer line management
            ('add_transferline', 'Can add transfer lines', 'Add Transfer Line'),
            ('change_transferline', 'Can change transfer lines', 'Change Transfer Line'),
            ('delete_transferline', 'Can delete transfer lines', 'Delete Transfer Line'),
            ('view_transferline', 'Can view transfer lines', 'View Transfer Line'),
            
            # Return management
            ('add_return', 'Can add returns', 'Add Return'),
            ('change_return', 'Can change returns', 'Change Return'),
            ('delete_return', 'Can delete returns', 'Delete Return'),
            ('view_return', 'Can view returns', 'View Return'),
            
            # Return line management
            ('add_returnline', 'Can add return lines', 'Add Return Line'),
            ('change_returnline', 'Can change return lines', 'Change Return Line'),
            ('delete_returnline', 'Can delete return lines', 'Delete Return Line'),
            ('view_returnline', 'Can view return lines', 'View Return Line'),
            
            # Promotion management
            ('add_promotion', 'Can add promotions', 'Add Promotion'),
            ('change_promotion', 'Can change promotions', 'Change Promotion'),
            ('delete_promotion', 'Can delete promotions', 'Delete Promotion'),
            ('view_promotion', 'Can view promotions', 'View Promotion'),
            
            # Coupon management
            ('add_coupon', 'Can add coupons', 'Add Coupon'),
            ('change_coupon', 'Can change coupons', 'Change Coupon'),
            ('delete_coupon', 'Can delete coupons', 'Delete Coupon'),
            ('view_coupon', 'Can view coupons', 'View Coupon'),
            
            # Purchase order management
            ('add_purchaseorder', 'Can add purchase orders', 'Add Purchase Order'),
            ('change_purchaseorder', 'Can change purchase orders', 'Change Purchase Order'),
            ('delete_purchaseorder', 'Can delete purchase orders', 'Delete Purchase Order'),
            ('view_purchaseorder', 'Can view purchase orders', 'View Purchase Order'),
            
            # Purchase order line management
            ('add_purchaseorderline', 'Can add purchase order lines', 'Add Purchase Order Line'),
            ('change_purchaseorderline', 'Can change purchase order lines', 'Change Purchase Order Line'),
            ('delete_purchaseorderline', 'Can delete purchase order lines', 'Delete Purchase Order Line'),
            ('view_purchaseorderline', 'Can view purchase order lines', 'View Purchase Order Line'),
            
            # Goods received note management
            ('add_goodsreceivednote', 'Can add goods received notes', 'Add Goods Received Note'),
            ('change_goodsreceivednote', 'Can change goods received notes', 'Change Goods Received Note'),
            ('delete_goodsreceivednote', 'Can delete goods received notes', 'Delete Goods Received Note'),
            ('view_goodsreceivednote', 'Can view goods received notes', 'View Goods Received Note'),
            
            # Goods received note line management
            ('add_goodsreceivednoteline', 'Can add goods received note lines', 'Add Goods Received Note Line'),
            ('change_goodsreceivednoteline', 'Can change goods received note lines', 'Change Goods Received Note Line'),
            ('delete_goodsreceivednoteline', 'Can delete goods received note lines', 'Delete Goods Received Note Line'),
            ('view_goodsreceivednoteline', 'Can view goods received note lines', 'View Goods Received Note Line'),
            
            # Report permissions
            ('view_sales_report', 'Can view sales reports', 'View Sales Report'),
            ('view_inventory_report', 'Can view inventory reports', 'View Inventory Report'),
            ('view_profitability_report', 'Can view profitability reports', 'View Profitability Report'),
            ('view_transfer_report', 'Can view transfer reports', 'View Transfer Report'),
            ('view_financial_reports', 'Can view financial reports', 'View Financial Reports'),
            ('view_payment_reports', 'Can view payment reports', 'View Payment Reports'),
            ('view_expense_reports', 'Can view expense reports', 'View Expense Reports'),
            
            # System permissions
            ('assign_roles', 'Can assign user roles', 'Assign Roles'),
            ('manage_permissions', 'Can manage user permissions', 'Manage Permissions'),
            ('view_user_activity', 'Can view user activity logs', 'View User Activity'),
            ('export_data', 'Can export data', 'Export Data'),
            ('reset_passwords', 'Can reset user passwords', 'Reset Passwords'),
            ('activate_deactivate_users', 'Can activate or deactivate users', 'Activate/Deactivate Users'),
        ]
        
        # Create permissions
        created_permissions = {}
        for codename, description, name in permissions_data:
            permission, created = Permission.objects.get_or_create(
                codename=codename,
                defaults={'name': name, 'description': description}
            )
            created_permissions[codename] = permission
            if created:
                self.stdout.write(f'Created permission: {name}')
            else:
                self.stdout.write(f'Permission already exists: {name}')
        
        # Define permission groups
        groups_data = [
            ('User Management', 'Permissions for managing users and accounts', [
                'add_user', 'change_user', 'delete_user', 'view_user'
            ]),
            ('Product Management', 'Permissions for managing products and categories', [
                'add_product', 'change_product', 'delete_product', 'view_product',
                'add_category', 'change_category', 'delete_category', 'view_category',
                'add_productvariant', 'change_productvariant', 'delete_productvariant', 'view_productvariant'
            ]),
            ('Inventory Management', 'Permissions for managing warehouses and inventory', [
                'add_warehouse', 'change_warehouse', 'delete_warehouse', 'view_warehouse',
                'add_inventory', 'change_inventory', 'delete_inventory', 'view_inventory'
            ]),
            ('Customer Management', 'Permissions for managing customers', [
                'add_customer', 'change_customer', 'delete_customer', 'view_customer'
            ]),
            ('Sales Management', 'Permissions for managing sales and payments', [
                'add_sale', 'change_sale', 'delete_sale', 'view_sale',
                'add_saleline', 'change_saleline', 'delete_saleline', 'view_saleline',
                'add_payment', 'change_payment', 'delete_payment', 'view_payment'
            ]),
            ('Transfer Management', 'Permissions for managing warehouse transfers', [
                'add_transfer', 'change_transfer', 'delete_transfer', 'view_transfer',
                'add_transferline', 'change_transferline', 'delete_transferline', 'view_transferline'
            ]),
            ('Returns Management', 'Permissions for managing returns and exchanges', [
                'add_return', 'change_return', 'delete_return', 'view_return',
                'add_returnline', 'change_returnline', 'delete_returnline', 'view_returnline'
            ]),
            ('Promotions Management', 'Permissions for managing promotions and coupons', [
                'add_promotion', 'change_promotion', 'delete_promotion', 'view_promotion',
                'add_coupon', 'change_coupon', 'delete_coupon', 'view_coupon'
            ]),
            ('Procurement Management', 'Permissions for managing purchase orders and goods received', [
                'add_purchaseorder', 'change_purchaseorder', 'delete_purchaseorder', 'view_purchaseorder',
                'add_purchaseorderline', 'change_purchaseorderline', 'delete_purchaseorderline', 'view_purchaseorderline',
                'add_goodsreceivednote', 'change_goodsreceivednote', 'delete_goodsreceivednote', 'view_goodsreceivednote',
                'add_goodsreceivednoteline', 'change_goodsreceivednoteline', 'delete_goodsreceivednoteline', 'view_goodsreceivednoteline'
            ]),
            ('Reporting', 'Permissions for viewing various reports', [
                'view_sales_report', 'view_inventory_report', 'view_profitability_report',
                'view_transfer_report', 'view_financial_reports', 'view_payment_reports',
                'view_expense_reports'
            ]),
            ('System Administration', 'Permissions for system administration', [
                'assign_roles', 'manage_permissions', 'view_user_activity', 'export_data',
                'reset_passwords', 'activate_deactivate_users'
            ])
        ]
        
        # Create permission groups
        for name, description, perm_codenames in groups_data:
            group, created = PermissionGroup.objects.get_or_create(
                name=name,
                defaults={'description': description}
            )
            
            # Get permissions for this group
            perms = [created_permissions[codename] for codename in perm_codenames 
                     if codename in created_permissions]
            group.permissions.set(perms)
            group.save()
            
            if created:
                self.stdout.write(f'Created permission group: {name} with {len(perms)} permissions')
            else:
                self.stdout.write(f'Permission group already exists: {name} with {len(perms)} permissions')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully seeded permissions system with {len(permissions_data)} permissions '
                f'and {len(groups_data)} permission groups'
            )
        )