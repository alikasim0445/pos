from rest_framework import serializers
from django.contrib.auth.models import User
from django.db import transaction
from .models import (
    UserProfile, Category, Product, ProductVariant, Warehouse, 
    Inventory, Customer, Sale, SaleLine, Payment, 
    Transfer, TransferLine, Return, ReturnLine, Promotion, Coupon, 
    PurchaseOrder, PurchaseOrderLine, GoodsReceivedNote, GoodsReceivedNoteLine, AuditLog
)


class CustomValidationError(serializers.ValidationError):
    def __init__(self, detail):
        if isinstance(detail, dict):
            super().__init__(detail)
        else:
            super().__init__({"error": detail})


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, required=True)
    role = serializers.ChoiceField(choices=UserProfile.ROLE_CHOICES, write_only=True, required=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'role', 'password', 'password_confirm']
        extra_kwargs = {
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True},
        }
    
    def validate(self, attrs):
        # Check if passwords match
        if attrs['password'] != attrs['password_confirm']:
            raise CustomValidationError({"password": "Password fields didn't match."})
        
        # Check if username already exists
        if User.objects.filter(username=attrs['username']).exists():
            raise CustomValidationError({"username": "A user with that username already exists."})
        
        # Check if email already exists
        if User.objects.filter(email=attrs['email']).exists():
            raise CustomValidationError({"email": "A user with that email already exists."})
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        # Extract registration-specific fields
        password_confirm = validated_data.pop('password_confirm', None)
        role = validated_data.pop('role')
        password = validated_data.pop('password')
        
        # Create user
        user = User.objects.create_user(
            username=validated_data.get('username'),
            email=validated_data.get('email'),
            first_name=validated_data.get('first_name'),
            last_name=validated_data.get('last_name'),
            password=password
        )
        
        # Ensure UserProfile exists and update role
        user_profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': role}
        )
        
        if not created:
            user_profile.role = role
            user_profile.save()
        
        return user


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer(read_only=True)
    role = serializers.CharField(source='userprofile.role', read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile', 'role', 'date_joined', 'is_active']
        read_only_fields = ['id', 'date_joined']
        extra_kwargs = {'password': {'write_only': True}}
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User(**validated_data)
        if password:
            user.set_password(password)
        user.save()
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        instance.save()
        return instance


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', required=False)
    email = serializers.CharField(source='user.email', required=False)
    first_name = serializers.CharField(source='user.first_name', required=False)
    last_name = serializers.CharField(source='user.last_name', required=False)
    
    class Meta:
        model = UserProfile
        fields = ['role', 'username', 'email', 'first_name', 'last_name']
    
    def validate_role(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            user = request.user
            if hasattr(user, 'userprofile'):
                if user.userprofile.role != 'super_admin' and value in ['super_admin', 'admin']:
                    raise CustomValidationError("You don't have permission to assign this role.")
        return value
    
    def update(self, instance, validated_data):
        user_data = validated_data.pop('user', {})
        
        # Update user profile
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update user
        user = instance.user
        for attr, value in user_data.items():
            setattr(user, attr, value)
        user.save()
        
        return instance


# Rest of your serializers remain the same...
class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'
    
    def validate_name(self, value):
        if not value.strip():
            raise CustomValidationError("Category name cannot be empty.")
        return value


class ProductVariantSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    
    class Meta:
        model = ProductVariant
        fields = '__all__'
    
    def validate_sku(self, value):
        if not value.strip():
            raise CustomValidationError("SKU cannot be empty.")
        return value


class ProductSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def validate_sku(self, value):
        if not value.strip():
            raise CustomValidationError("SKU cannot be empty.")
        return value
    
    def validate_price(self, value):
        if value <= 0:
            raise CustomValidationError("Price must be greater than zero.")
        return value


class ProductDetailSerializer(serializers.ModelSerializer):
    variants = ProductVariantSerializer(many=True, read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    total_inventory = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = '__all__'
    
    def get_total_inventory(self, obj):
        from django.db.models import Sum
        total = obj.inventory_set.aggregate(
            total_on_hand=Sum('qty_on_hand') or 0,
            total_reserved=Sum('qty_reserved') or 0,
            total_available=(Sum('qty_on_hand') or 0) - (Sum('qty_reserved') or 0)
        )
        return total


class WarehouseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Warehouse
        fields = '__all__'
    
    def validate_name(self, value):
        if not value.strip():
            raise CustomValidationError("Warehouse name cannot be empty.")
        return value


class InventorySerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    available_stock = serializers.IntegerField(read_only=True)
    
    class Meta:
        model = Inventory
        fields = '__all__'
    
    def validate(self, attrs):
        qty_on_hand = attrs.get('qty_on_hand', self.instance.qty_on_hand if self.instance else 0)
        qty_reserved = attrs.get('qty_reserved', self.instance.qty_reserved if self.instance else 0)
        
        if qty_reserved > qty_on_hand:
            raise CustomValidationError({
                "qty_reserved": "Reserved quantity cannot exceed quantity on hand."
            })
        
        return attrs


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = '__all__'
    
    def validate_email(self, value):
        if value and Customer.objects.filter(email=value).exclude(id=self.instance.id if self.instance else None).exists():
            raise CustomValidationError("A customer with this email already exists.")
        return value


class SaleLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    
    class Meta:
        model = SaleLine
        fields = '__all__'
    
    def validate_quantity(self, value):
        if value <= 0:
            raise CustomValidationError("Quantity must be greater than zero.")
        return value
    
    def validate_unit_price(self, value):
        if value <= 0:
            raise CustomValidationError("Unit price must be greater than zero.")
        return value


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = '__all__'
    
    def validate_amount(self, value):
        if value <= 0:
            raise CustomValidationError("Payment amount must be greater than zero.")
        return value


class SaleSerializer(serializers.ModelSerializer):
    lines = SaleLineSerializer(many=True)
    payments = PaymentSerializer(many=True, read_only=True)
    cashier_name = serializers.CharField(source='cashier.get_full_name', read_only=True)
    customer_name = serializers.CharField(source='customer.__str__', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    
    class Meta:
        model = Sale
        fields = '__all__'
    
    def validate(self, attrs):
        lines_data = attrs.get('lines', [])
        if not lines_data:
            raise CustomValidationError({"lines": "Sale must have at least one line item."})
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop('lines', [])
        sale = Sale.objects.create(**validated_data)
        
        for line_data in lines_data:
            SaleLine.objects.create(sale=sale, **line_data)
        
        return sale
    
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                SaleLine.objects.create(sale=instance, **line_data)
        
        return instance


class TransferLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    
    class Meta:
        model = TransferLine
        fields = '__all__'
    
    def validate_requested_qty(self, value):
        if value <= 0:
            raise CustomValidationError("Requested quantity must be greater than zero.")
        return value


class TransferSerializer(serializers.ModelSerializer):
    lines = TransferLineSerializer(many=True)
    from_warehouse_name = serializers.CharField(source='from_warehouse.name', read_only=True)
    to_warehouse_name = serializers.CharField(source='to_warehouse.name', read_only=True)
    requested_by_name = serializers.CharField(source='requested_by.get_full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = Transfer
        fields = '__all__'
    
    def validate(self, attrs):
        from_warehouse = attrs.get('from_warehouse')
        to_warehouse = attrs.get('to_warehouse')
        
        if from_warehouse and to_warehouse and from_warehouse == to_warehouse:
            raise CustomValidationError({
                "from_warehouse": "Source and destination warehouses cannot be the same."
            })
        
        lines_data = attrs.get('lines', [])
        if not lines_data:
            raise CustomValidationError({"lines": "Transfer must have at least one line item."})
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        transfer = Transfer.objects.create(**validated_data)
        
        for line_data in lines_data:
            TransferLine.objects.create(transfer=transfer, **line_data)
        
        return transfer
    
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                TransferLine.objects.create(transfer=instance, **line_data)
        
        return instance


class ReturnLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    exchange_product_name = serializers.CharField(source='exchange_product.name', read_only=True)
    exchange_variant_name = serializers.CharField(source='exchange_variant.name', read_only=True)
    
    class Meta:
        model = ReturnLine
        fields = '__all__'
    
    def validate_quantity(self, value):
        if value <= 0:
            raise CustomValidationError("Quantity must be greater than zero.")
        return value


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = '__all__'
        read_only_fields = ('created_at', 'updated_at', 'used_count')
    
    def validate(self, attrs):
        promotion_type = attrs.get('promotion_type')
        
        if promotion_type == 'buy_x_get_y':
            buy_qty = attrs.get('buy_quantity')
            get_qty = attrs.get('get_quantity')
            
            if not buy_qty or not get_qty:
                raise CustomValidationError({
                    "buy_quantity": "Buy and get quantities are required for this promotion type.",
                    "get_quantity": "Buy and get quantities are required for this promotion type."
                })
        
        if promotion_type in ['percentage', 'fixed_amount']:
            discount_value = attrs.get('discount_value')
            if not discount_value or discount_value <= 0:
                raise CustomValidationError({
                    "discount_value": "Discount value must be greater than zero."
                })
        
        return attrs


class PurchaseOrderLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='product.name', read_only=True)
    variant_name = serializers.CharField(source='variant.name', read_only=True)
    
    class Meta:
        model = PurchaseOrderLine
        fields = '__all__'
        read_only_fields = ('total_price', 'processed_qty')
    
    def validate_ordered_qty(self, value):
        if value <= 0:
            raise CustomValidationError("Ordered quantity must be greater than zero.")
        return value
    
    def validate_unit_cost(self, value):
        if value <= 0:
            raise CustomValidationError("Unit cost must be greater than zero.")
        return value


class PurchaseOrderSerializer(serializers.ModelSerializer):
    lines = PurchaseOrderLineSerializer(many=True)
    supplier_name = serializers.CharField(source='supplier.get_full_name', read_only=True)
    warehouse_name = serializers.CharField(source='warehouse.name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.get_full_name', read_only=True)
    
    class Meta:
        model = PurchaseOrder
        fields = '__all__'
        read_only_fields = ('po_number', 'created_at', 'updated_at', 'subtotal', 'total_amount')
    
    def validate(self, attrs):
        lines_data = attrs.get('lines', [])
        if not lines_data:
            raise CustomValidationError({"lines": "Purchase order must have at least one line item."})
        
        # Validate expected delivery date
        order_date = attrs.get('order_date')
        expected_delivery_date = attrs.get('expected_delivery_date')
        
        if expected_delivery_date and order_date and expected_delivery_date <= order_date:
            raise CustomValidationError({
                "expected_delivery_date": "Expected delivery date must be after order date."
            })
        
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        po = PurchaseOrder.objects.create(**validated_data)
        
        for line_data in lines_data:
            PurchaseOrderLine.objects.create(purchase_order=po, **line_data)
        
        # Calculate totals after creating lines
        po.calculate_totals()
        
        return po
    
    @transaction.atomic
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        # Update the purchase order fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update or replace the lines if provided
        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                PurchaseOrderLine.objects.create(purchase_order=instance, **line_data)
            
            # Recalculate totals after updating lines
            instance.calculate_totals()
        
        return instance


class GoodsReceivedNoteLineSerializer(serializers.ModelSerializer):
    product_name = serializers.CharField(source='purchase_order_line.product.name', read_only=True)
    ordered_qty = serializers.IntegerField(source='purchase_order_line.ordered_qty', read_only=True)
    received_so_far = serializers.IntegerField(source='purchase_order_line.received_qty', read_only=True)
    
    class Meta:
        model = GoodsReceivedNoteLine
        fields = '__all__'
        
    def validate_received_qty(self, value):
        if value <= 0:
            raise CustomValidationError("Received quantity must be greater than zero.")
        return value


class GoodsReceivedNoteSerializer(serializers.ModelSerializer):
    lines = GoodsReceivedNoteLineSerializer(many=True)
    po_number = serializers.CharField(source='purchase_order.po_number', read_only=True)
    received_by_name = serializers.CharField(source='received_by.get_full_name', read_only=True)
    verified_by_name = serializers.CharField(source='verified_by.get_full_name', read_only=True)
    
    class Meta:
        model = GoodsReceivedNote
        fields = '__all__'
        read_only_fields = ('grn_number', 'created_at', 'received_date')
    
    def validate(self, attrs):
        lines_data = attrs.get('lines', [])
        if not lines_data:
            raise CustomValidationError({"lines": "GRN must have at least one line item."})
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        grn = GoodsReceivedNote.objects.create(**validated_data)
        
        for line_data in lines_data:
            GoodsReceivedNoteLine.objects.create(grn=grn, **line_data)
        
        return grn


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = '__all__'
        read_only_fields = ('code', 'created_at', 'updated_at', 'used_count')
    
    def validate(self, attrs):
        discount_value = attrs.get('discount_value')
        if discount_value and discount_value <= 0:
            raise CustomValidationError({
                "discount_value": "Discount value must be greater than zero."
            })
        
        return attrs


class ReturnSerializer(serializers.ModelSerializer):
    lines = ReturnLineSerializer(many=True)
    original_sale_receipt = serializers.CharField(source='original_sale.receipt_number', read_only=True)
    customer_name = serializers.CharField(source='customer.__str__', read_only=True)
    processed_by_name = serializers.CharField(source='processed_by.get_full_name', read_only=True)
    
    class Meta:
        model = Return
        fields = '__all__'
        read_only_fields = ('return_number', 'created_at', 'updated_at')
    
    def validate(self, attrs):
        lines_data = attrs.get('lines', [])
        if not lines_data:
            raise CustomValidationError({"lines": "Return must have at least one line item."})
        return attrs
    
    @transaction.atomic
    def create(self, validated_data):
        lines_data = validated_data.pop('lines')
        return_obj = Return.objects.create(**validated_data)
        
        for line_data in lines_data:
            ReturnLine.objects.create(return_obj=return_obj, **line_data)
        
        return return_obj
    
    def update(self, instance, validated_data):
        lines_data = validated_data.pop('lines', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if lines_data is not None:
            instance.lines.all().delete()
            for line_data in lines_data:
                ReturnLine.objects.create(return_obj=instance, **line_data)
        
        return instance


class AuditLogSerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_username = serializers.CharField(source='user.username', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = '__all__'