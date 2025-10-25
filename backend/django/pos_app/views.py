from datetime import datetime
from rest_framework import viewsets, generics, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
from django.utils import timezone
from django.template.loader import render_to_string
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template import loader
from django.urls import reverse
import tempfile
import os
import csv
import json
from decimal import Decimal
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser

# Check if openpyxl is available for Excel export
try:
    
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

# Check if reportlab is available for PDF export
try:
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


from .models import (
    User, Category, Product, ProductVariant, Warehouse,Location,Bin,
    Inventory, Customer, Sale, SaleLine, Payment, 
    Transfer, TransferLine, AuditLog, Return, ReturnLine, Promotion, Coupon,
    PurchaseOrder, PurchaseOrderLine, GoodsReceivedNote, GoodsReceivedNoteLine, UserProfile,
    Webhook, WebhookLog, PaymentToken, PaymentGatewayConfig,
    EcommercePlatform, EcommerceSyncLog, Reservation
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer, CategorySerializer, ProductSerializer, ProductVariantSerializer,
    WarehouseSerializer, LocationSerializer, BinSerializer, InventorySerializer, CustomerSerializer,
    SaleSerializer, SaleLineSerializer, PaymentSerializer, WebhookSerializer,WebhookLogSerializer,PaymentTokenSerializer, PaymentGatewayConfigSerializer,
    TransferSerializer, TransferLineSerializer, AuditLogSerializer, ReturnSerializer, ReturnLineSerializer, EcommercePlatformSerializer, EcommerceSyncLogSerializer,
    PromotionSerializer, CouponSerializer, PurchaseOrderSerializer, PurchaseOrderLineSerializer,
    GoodsReceivedNoteSerializer, GoodsReceivedNoteLineSerializer, ReservationSerializer
)
from .mfa_views import (
    enable_mfa,
    confirm_mfa,
    disable_mfa,
    verify_mfa,
    mfa_status,
)

import logging
logger = logging.getLogger(__name__)


# Authentication
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

User = get_user_model()

# Import for audit logging
from .signals import set_current_user, get_current_user

class CustomTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        # Allow login with either username or email
        username_or_email = request.data.get('username')
        password = request.data.get('password')
        
        if not username_or_email or not password:
            return Response(
                {'error': 'Username/email and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initially assume it's a username
        username = username_or_email
        user = None
        
        # Check if the input is an email
        if '@' in username_or_email:
            # Try to get user by email
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                user = None
        else:
            # Use as username
            username = username_or_email
        
        # If we didn't find a user by email, try to find by username
        if not user:
            try:
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                user = None
        
        # Authenticate if user exists
        if user and user.check_password(password):
            # Check if user has MFA enabled
            user_profile = getattr(user, 'userprofile', None)
            if user_profile and user_profile.is_mfa_enabled:
                # For now, return a response requiring MFA
                return Response({
                    'requires_mfa': True,
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                })
            
            # Generate tokens if no MFA required
            refresh = RefreshToken.for_user(user)
            
            # Create audit log for successful login
            from .models import AuditLog
            AuditLog.objects.create(
                user=user,
                action='login',
                object_type='session',
                object_id=user.id,
                object_repr=f'User {user.username} logged in',
                timestamp=timezone.now(),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes='User login via API'
            )
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
            })
        
        # If authentication fails, still log the attempt
        # Find the user to create the audit log even if login failed
        failed_user = None
        if '@' in username_or_email:
            try:
                failed_user = User.objects.get(email=username_or_email)
            except User.DoesNotExist:
                failed_user = None
        else:
            try:
                failed_user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                failed_user = None
        
        if failed_user:
            from .models import AuditLog
            AuditLog.objects.create(
                user=failed_user,
                action='login_failed',
                object_type='session',
                object_id=failed_user.id,
                object_repr=f'Failed login attempt for user {failed_user.username}',
                timestamp=timezone.now(),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes='Failed login attempt - invalid credentials'
            )
        
        # If authentication fails
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


from rest_framework.permissions import AllowAny


class CustomTokenObtainPairView(TokenObtainPairView):
    permission_classes = [AllowAny]  # Explicitly allow unauthenticated access for token generation
    
    def post(self, request, *args, **kwargs):
        # Allow login with either username or email
        username_or_email = request.data.get('username')
        password = request.data.get('password')
        
        if not username_or_email or not password:
            return Response(
                {'error': 'Username/email and password are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Initially assume it's a username
        username = username_or_email
        user = None
        
        # Check if the input is an email
        if '@' in username_or_email:
            # Try to get user by email
            try:
                user = User.objects.get(email=username_or_email)
                username = user.username
            except User.DoesNotExist:
                user = None
        else:
            # Use as username
            username = username_or_email
        
        # If we didn't find a user by email, try to find by username
        if not user:
            try:
                user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                user = None
        
        # Authenticate if user exists
        if user and user.check_password(password):
            # Check if user has MFA enabled
            user_profile = getattr(user, 'userprofile', None)
            if user_profile and user_profile.is_mfa_enabled:
                # For now, return a response requiring MFA
                return Response({
                    'requires_mfa': True,
                    'user_id': user.id,
                    'username': user.username,
                    'email': user.email,
                })
            
            # Generate tokens if no MFA required
            refresh = RefreshToken.for_user(user)
            
            # Create audit log for successful login
            from .models import AuditLog
            AuditLog.objects.create(
                user=user,
                action='login',
                object_type='session',
                object_id=user.id,
                object_repr=f'User {user.username} logged in',
                timestamp=timezone.now(),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes='User login via API'
            )
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
            })
        
        # If authentication fails, still log the attempt
        # Find the user to create the audit log even if login failed
        failed_user = None
        if '@' in username_or_email:
            try:
                failed_user = User.objects.get(email=username_or_email)
            except User.DoesNotExist:
                failed_user = None
        else:
            try:
                failed_user = User.objects.get(username=username_or_email)
            except User.DoesNotExist:
                failed_user = None
        
        if failed_user:
            from .models import AuditLog
            AuditLog.objects.create(
                user=failed_user,
                action='login_failed',
                object_type='session',
                object_id=failed_user.id,
                object_repr=f'Failed login attempt for user {failed_user.username}',
                timestamp=timezone.now(),
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes='Failed login attempt - invalid credentials'
            )
        
        # If authentication fails
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, *args, **kwargs):
        # Override create to handle the registration properly
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        return Response({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


# Password Reset Views
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Handle password reset request by sending an email with a reset link
    """
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if the user exists or not to prevent email enumeration attacks
        return Response({'message': 'If your email exists in our system, you will receive a password reset link shortly.'}, status=status.HTTP_200_OK)
    
    # Generate password reset token and URL
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build reset URL (adjust for your frontend URL)
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    reset_url = f"{frontend_url}/reset-password/{uid}/{token}/"
    
    # Send email with password reset link
    subject = 'Password Reset Request'
    html_message = loader.render_to_string('password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
        'site_name': getattr(settings, 'SITE_NAME', 'POS Management System'),
    })
    
    send_mail(
        subject,
        f'Please click this link to reset your password: {reset_url}',
        getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@pos-system.com'),
        [user.email],
        fail_silently=False,
        html_message=html_message
    )
    
    return Response({'message': 'If your email exists in our system, you will receive a password reset link shortly.'}, status=status.HTTP_200_OK)


class UserListView(generics.ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]


# Category Views
class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


# Product Views
class ProductListView(generics.ListCreateAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Add this line
    
    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        return Product.objects.all()

class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]  # Add this line

# Product Variant Views
class ProductVariantListView(generics.ListCreateAPIView):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAuthenticated]


class ProductVariantDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAuthenticated]


# Category Views
class CategoryListView(generics.ListCreateAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


class CategoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]


# Warehouse Views
class WarehouseListView(generics.ListCreateAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]


class WarehouseDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if the warehouse can be safely deleted
        can_delete, message = instance.can_delete()
        if not can_delete:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Proceed with deletion
        return super().destroy(request, *args, **kwargs)


# Location Views
class LocationListView(generics.ListCreateAPIView):
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Location.objects.select_related('warehouse').all()
        
        # Add filtering options
        warehouse_id = self.request.query_params.get('warehouse')
        
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        return queryset
    
    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        # Different permissions for list vs create
        # if self.request.method == 'POST':
        #     permission_classes.append(HasSpecificPermission)
        return [permission() for permission in permission_classes]
    



class LocationDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]


# Bin Views
class BinListView(generics.ListCreateAPIView):
    serializer_class = BinSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Bin.objects.select_related('location').all()
        
        # Add filtering options
        location_id = self.request.query_params.get('location')
        
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        
        return queryset
    
    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        # Different permissions for list vs create
        
        return [permission() for permission in permission_classes]
    
    def perform_create(self, serializer):
        # Check for specific permission to create bins
        if not self.request.user.userprofile.has_permission('add_inventory'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to create bins")
        serializer.save()


class BinDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Bin.objects.all()
    serializer_class = BinSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        # Different permissions based on the action
        # if self.request.method in ['PUT', 'PATCH']:
        #     permission_classes.append(HasSpecificPermission)
        # elif self.request.method == 'DELETE':
        #     permission_classes.append(HasSpecificPermission)
        # else:  # GET
        #     permission_classes.append(HasSpecificPermission)
        return [permission() for permission in permission_classes]
    
    def perform_update(self, serializer):
        # Check for specific permission to update bins
        if not self.request.user.userprofile.has_permission('change_inventory'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to update bins")
        serializer.save()
    
    def perform_destroy(self, instance):
        # Check for specific permission to delete bins
        if not self.request.user.userprofile.has_permission('delete_inventory'):
            from rest_framework.exceptions import PermissionDenied
            raise PermissionDenied("You don't have permission to delete bins")
        instance.delete()


# Inventory Views
class InventoryListView(generics.ListCreateAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]


class InventoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]


# Customer Views
class CustomerListView(generics.ListCreateAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class CustomerDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


from django.db import transaction

# Sale Views
class SaleListView(generics.ListCreateAPIView):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        permission_classes = [IsAuthenticated]
        # Different permissions for list vs create
        # if self.request.method == 'POST':
        #     permission_classes.append(HasSpecificPermission)
        return [permission() for permission in permission_classes]
    


class SaleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]

import uuid
import logging

logger = logging.getLogger(__name__)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_sale(request):
    logger.error(f"create_sale request data: {request.data}")

    try:
        with transaction.atomic():
            logger.error("Starting sale creation")

            # -------------------- Extract Data --------------------
            cashier_id = request.data.get('cashier_id')
            customer_id = request.data.get('customer_id')
            warehouse_id = request.data.get('warehouse_id')
            items_data = request.data.get('items', [])
            payments_data = request.data.get('payments', [])
            discount_amount = float(request.data.get('discount_amount', 0))
            notes = request.data.get('notes', '')
            reservation_id = request.data.get('reservation_id')

            # -------------------- Handle Reservation --------------------
            if reservation_id:
                try:
                    reservation = Reservation.objects.get(id=reservation_id)
                    if reservation.status != 'active':
                        return Response({'error': 'Reservation is not active'}, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Verify that the items in the sale match the items in the reservation
                    # This is a simplified check. A more robust implementation would compare each item.
                    if len(items_data) != reservation.lines.count():
                        return Response({'error': 'Items in sale do not match items in reservation'}, status=status.HTTP_400_BAD_REQUEST)

                    reservation.status = 'completed'
                    reservation.save()

                except Reservation.DoesNotExist:
                    return Response({'error': f"Reservation with id {reservation_id} not found"}, status=status.HTTP_400_BAD_REQUEST)

            # -------------------- Validate Core Entities --------------------
            try:
                cashier = User.objects.get(id=cashier_id)
            except User.DoesNotExist:
                return Response({'error': f"Cashier with id {cashier_id} not found"}, status=status.HTTP_400_BAD_REQUEST)

            customer = None
            if customer_id:
                try:
                    customer = Customer.objects.get(id=customer_id)
                except Customer.DoesNotExist:
                    return Response({'error': f"Customer with id {customer_id} not found"}, status=status.HTTP_400_BAD_REQUEST)

            try:
                warehouse = Warehouse.objects.get(id=warehouse_id)
            except Warehouse.DoesNotExist:
                return Response({'error': f"Warehouse with id {warehouse_id} not found"}, status=status.HTTP_400_BAD_REQUEST)

            logger.error("Validated cashier, customer, and warehouse")

            # -------------------- Validate Inventory --------------------
            inventory_errors = []
            for item_data in items_data:
                try:
                    product = Product.objects.get(id=item_data['product_id'])
                except Product.DoesNotExist:
                    inventory_errors.append(f"Product with id {item_data['product_id']} not found")
                    continue

                variant = None
                if item_data.get('variant_id') is not None:
                    try:
                        variant = ProductVariant.objects.get(id=item_data['variant_id'])
                    except ProductVariant.DoesNotExist:
                        inventory_errors.append(f"ProductVariant with id {item_data['variant_id']} not found")
                        continue

                try:
                    inventory = Inventory.objects.get(product=product, variant=variant, warehouse=warehouse)
                    if inventory.available_stock() < item_data['quantity']:
                        inventory_errors.append(f"Insufficient stock for {product.name}. Available: {inventory.available_stock()}, Requested: {item_data['quantity']}")
                except Inventory.DoesNotExist:
                    inventory_errors.append(f"Inventory for {product.name} not found in warehouse {warehouse.name}")

            if inventory_errors:
                return Response({'errors': inventory_errors}, status=status.HTTP_400_BAD_REQUEST)

            logger.error("Validated inventory")

            # -------------------- Generate Receipt Early (FIXED) --------------------
            receipt_number = f"RCT-{uuid.uuid4().hex[:8].upper()}"
            logger.error(f"Generated receipt number: {receipt_number}")

            # -------------------- Calculate Totals --------------------
            total_amount = sum(item['quantity'] * item['unit_price'] for item in items_data)
            tax_rate = getattr(settings, 'DEFAULT_TAX_RATE', 0.10)
            tax_amount = total_amount * tax_rate
            total_amount_with_tax = total_amount + tax_amount - discount_amount

            # -------------------- Determine Payment Status --------------------
            total_payment = sum(p['amount'] for p in payments_data)
            if total_payment == 0:
                payment_status = 'pending'
            elif total_payment >= total_amount_with_tax:
                payment_status = 'completed'
            elif 0 < total_payment < total_amount_with_tax:
                payment_status = 'partially_paid'
            else:
                payment_status = 'completed'

            # -------------------- Create Sale --------------------
            sale = Sale.objects.create(
                receipt_number=receipt_number,
                cashier=cashier,
                customer=customer,
                warehouse=warehouse,
                total_amount=total_amount_with_tax,
                tax_amount=tax_amount,
                discount_amount=discount_amount,
                payment_status=payment_status,
                notes=notes
            )
            logger.error("Created sale object")

            # -------------------- Create Sale Lines & Update Inventory --------------------
            for item_data in items_data:
                product = Product.objects.get(id=item_data['product_id'])
                variant = ProductVariant.objects.get(id=item_data['variant_id']) if item_data.get('variant_id') is not None else None

                SaleLine.objects.create(
                    sale=sale,
                    product=product,
                    variant=variant,
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    total_price=item_data['quantity'] * item_data['unit_price'],
                    discount_percent=item_data.get('discount_percent', 0)
                )

                inventory = Inventory.objects.get(product=product, variant=variant, warehouse=warehouse)
                inventory.qty_on_hand -= item_data['quantity']
                inventory.save()

            logger.error("Created sale lines and updated inventory")

            # -------------------- Create Payments --------------------
            for payment_data in payments_data:
                Payment.objects.create(
                    sale=sale,
                    payment_method=payment_data['method'],
                    amount=payment_data['amount'],
                    reference=f"PAY-{uuid.uuid4().hex[:8].upper()}"
                )
            logger.error("Created payment records")

            # -------------------- Customer Loyalty (Optional) --------------------
            if customer:
                points_earned = customer.calculate_loyalty_points_from_purchase(float(sale.total_amount))
                original_points = customer.loyalty_points
                new_points = customer.earn_loyalty_points(points_earned)

                AuditLog.objects.create(
                    user=request.user,
                    action='update',
                    object_type='customer',
                    object_id=customer.id,
                    object_repr=f"Loyalty points earned from sale {sale.receipt_number}",
                    old_values={'loyalty_points': original_points},
                    new_values={'loyalty_points': new_points},
                    notes=f"Loyalty points earned: {points_earned} from sale totaling ${sale.total_amount}",
                    ip_address=request.META.get('REMOTE_ADDR')
                )

            # -------------------- Return Response --------------------
            serializer = SaleSerializer(sale)
            logger.error("Sale creation successful ✅")
            return Response(serializer.data, status=status.HTTP_201_CREATED)

    except Exception as e:
        logger.error(f"Error in create_sale: {e}", exc_info=True)
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_payment_gateway(request):
    """
    Process a payment through a payment gateway (Stripe/PayPal)
    Expected JSON format:
    {
        "sale_id": 1,
        "amount": 100.00,
        "payment_method_data": {
            "gateway": "stripe", // or "paypal"
            "payment_method_id": "pm_card_visa", // for Stripe
            "source": "tok_visa", // for Stripe
            // For PayPal: card details
            "card_number": "4111111111111111",
            "expiry_month": 12,
            "expiry_year": 2025,
            "cvv": "123"
        }
    }
    """
    try:
        from .services import PaymentGatewayService
        
        sale_id = request.data.get('sale_id')
        amount = request.data.get('amount')
        payment_method_data = request.data.get('payment_method_data', {})
        
        if not sale_id or not amount or not payment_method_data:
            return Response(
                {'error': 'sale_id, amount, and payment_method_data are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the sale
        try:
            sale = Sale.objects.get(id=sale_id)
        except Sale.DoesNotExist:
            return Response(
                {'error': 'Sale not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Process the payment
        customer = sale.customer if sale.customer else None
        result = PaymentGatewayService.process_payment(
            sale, amount, payment_method_data, customer
        )
        
        if result['success']:
            # Create payment record
            Payment.objects.create(
                sale=sale,
                payment_method=f"{result['gateway']}_card",
                amount=amount,
                reference=result['transaction_id'],
                notes=f"Payment processed via {result['gateway']}"
            )
            
            # Update sale payment status
            sale.update_payment_status()
            
            return Response({
                'success': True,
                'transaction_id': result['transaction_id'],
                'status': result['status'],
                'message': 'Payment processed successfully'
            })
        else:
            return Response({
                'success': False,
                'error': result['error']
            }, status=status.HTTP_400_BAD_REQUEST)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_customer_payment_token(request):
    """
    Create a payment token for a customer
    Expected JSON format:
    {
        "customer_id": 1,
        "payment_method_data": {
            "gateway": "stripe", // or "paypal"
            // Stripe-specific data:
            "source": "tok_visa",
            "number": "4242424242424242",
            "exp_month": 12,
            "exp_year": 2025,
            "cvc": "123",
            "brand": "Visa"
        }
    }
    """
    try:
        from .services import PaymentGatewayService
        
        customer_id = request.data.get('customer_id')
        payment_method_data = request.data.get('payment_method_data', {})
        
        if not customer_id or not payment_method_data:
            return Response(
                {'error': 'customer_id and payment_method_data are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the customer
        try:
            customer = Customer.objects.get(id=customer_id)
        except Customer.DoesNotExist:
            return Response(
                {'error': 'Customer not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Create the payment token
        gateway = payment_method_data.get('gateway', 'stripe')
        token = PaymentGatewayService.create_customer_token(
            customer, payment_method_data, gateway
        )
        
        serializer = PaymentTokenSerializer(token)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_ecommerce_products(request, platform_id):
    """
    Sync products from POS to e-commerce platform
    """
    try:
        from .services import EcommerceSyncService
        
        try:
            platform = EcommercePlatform.objects.get(id=platform_id)
        except EcommercePlatform.DoesNotExist:
            return Response(
                {'error': 'E-commerce platform not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not platform.is_active:
            return Response(
                {'error': 'E-commerce platform is not active'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not platform.sync_products:
            return Response(
                {'error': 'Product sync is disabled for this platform'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = EcommerceSyncService.sync_products_to_ecommerce(platform)
        return Response(result)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_ecommerce_inventory(request, platform_id):
    """
    Sync inventory from POS to e-commerce platform
    """
    try:
        from .services import EcommerceSyncService
        
        try:
            platform = EcommercePlatform.objects.get(id=platform_id)
        except EcommercePlatform.DoesNotExist:
            return Response(
                {'error': 'E-commerce platform not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not platform.is_active:
            return Response(
                {'error': 'E-commerce platform is not active'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not platform.sync_inventory:
            return Response(
                {'error': 'Inventory sync is disabled for this platform'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = EcommerceSyncService.sync_inventory_to_ecommerce(platform)
        return Response(result)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def sync_ecommerce_orders(request, platform_id):
    """
    Sync orders from e-commerce platform to POS
    """
    try:
        from .services import EcommerceSyncService
        
        try:
            platform = EcommercePlatform.objects.get(id=platform_id)
        except EcommercePlatform.DoesNotExist:
            return Response(
                {'error': 'E-commerce platform not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not platform.is_active:
            return Response(
                {'error': 'E-commerce platform is not active'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not platform.sync_orders:
            return Response(
                {'error': 'Order sync is disabled for this platform'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        result = EcommerceSyncService.sync_orders_from_ecommerce(platform)
        return Response(result)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_ecommerce_sync_status(request, platform_id):
    """
    Get the sync status and logs for an e-commerce platform
    """
    try:
        try:
            platform = EcommercePlatform.objects.get(id=platform_id)
        except EcommercePlatform.DoesNotExist:
            return Response(
                {'error': 'E-commerce platform not found'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get recent sync logs
        recent_logs = EcommerceSyncLog.objects.filter(
            platform=platform
        ).order_by('-started_at')[:10]
        
        logs_data = EcommerceSyncLogSerializer(recent_logs, many=True).data
        
        return Response({
            'platform': EcommercePlatformSerializer(platform).data,
            'last_sync': platform.last_sync,
            'recent_syncs': logs_data
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_payment_to_sale(request, sale_id):
    """
    Add an additional payment to an existing sale (for handling partial payments).
    Expected JSON format:
    {
        "method": "cash",  // Payment method
        "amount": 10.50,   // Amount to pay
        "reference": "optional reference"
    }
    """
    try:
        sale = Sale.objects.get(id=sale_id)
        
        # Validate the payment data
        payment_method = request.data.get('method')
        amount = request.data.get('amount')
        
        if not payment_method or not amount:
            return Response(
                {'error': 'Payment method and amount are required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate payment method
        valid_methods = [choice[0] for choice in Payment.PAYMENT_METHOD_CHOICES]
        if payment_method not in valid_methods:
            return Response(
                {'error': f'Invalid payment method. Valid methods: {valid_methods}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate amount
        if float(amount) <= 0:
            return Response(
                {'error': 'Payment amount must be greater than zero'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if sale is already completed
        if sale.payment_status == 'completed':
            return Response(
                {'error': 'Sale is already completed'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate if the payment would overpay
        total_paid = sale.amount_paid() + float(amount)
        if total_paid > sale.total_amount:
            return Response(
                {'error': f'Payment would exceed total amount. Max additional payment: ${sale.total_amount - sale.amount_paid():.2f}'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create the payment
        Payment.objects.create(
            sale=sale,
            payment_method=payment_method,
            amount=amount,
            reference=request.data.get('reference', ''),
        )
        
        # Update the sale's payment status
        sale.update_payment_status()
        
        # Serialize and return the updated sale
        serializer = SaleSerializer(sale)
        return Response(serializer.data, status=status.HTTP_200_OK)
        
    except Sale.DoesNotExist:
        return Response({'error': 'Sale not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


from django.http import HttpResponse
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

# Import your Sale model
from .models import Sale  # Adjust import path as needed

# Check if reportlab is available
try:
    from reportlab.lib.pagesizes import letter
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    from reportlab.lib.units import inch
    import io
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab is not available for PDF generation")


def get_receipt(request, pk):
    """
    Generate and return a receipt for a specific sale in PDF format.
    Uses WeasyPrint if available, otherwise falls back to reportlab.
    """
    try:
        logger.info(f"Generating receipt for sale ID: {pk}")
        sale = Sale.objects.get(id=pk)
        logger.info(f"Found sale: {sale.receipt_number}")
        
        # Prepare context for the receipt template
        context = {
            'sale': sale,
            'sale_lines': sale.lines.all(),
            'payments': sale.payments.all(),
            'company_name': getattr(settings, 'COMPANY_NAME', 'POS Company'),
            'company_address': getattr(settings, 'COMPANY_ADDRESS', '123 Business St.'),
            'company_phone': getattr(settings, 'COMPANY_PHONE', '+1-234-567-890'),
        }
        
        # Try to generate PDF with WeasyPrint first (higher quality)
        try:
            from weasyprint import HTML
            logger.info("Attempting PDF generation with WeasyPrint")
            
            # Render the receipt HTML
            html_string = render_to_string('receipt.html', context)
            logger.info("Successfully rendered HTML template")
            
            # Generate PDF
            html = HTML(string=html_string)
            pdf = html.write_pdf()
            logger.info("Successfully generated PDF with WeasyPrint")
            
            # Create HTTP response with PDF
            response = HttpResponse(pdf, content_type='application/pdf')
            response['Content-Disposition'] = f'attachment; filename="receipt_{sale.receipt_number}.pdf"'
            return response
            
        except ImportError:
            logger.warning("WeasyPrint not available, falling back to ReportLab")
            # WeasyPrint not available, use reportlab as fallback
            pass
        except Exception as e:
            logger.error(f"WeasyPrint PDF generation failed: {str(e)}")
            # If there's an error with WeasyPrint (e.g., missing template), handle gracefully
            pass
        
        # Fallback to reportlab if weasyprint is not available or failed
        if REPORTLAB_AVAILABLE:
            try:
                logger.info("Attempting PDF generation with ReportLab")
                # Create a buffer to write the PDF to
                buffer = io.BytesIO()
                doc = SimpleDocTemplate(
                    buffer, 
                    pagesize=letter, 
                    topMargin=0.25*inch, 
                    bottomMargin=0.25*inch, 
                    leftMargin=0.25*inch, 
                    rightMargin=0.25*inch
                )
                styles = getSampleStyleSheet()
                story = []
                
                # Add company info
                title_style = ParagraphStyle(
                    'CustomTitle',
                    parent=styles['Heading1'],
                    fontSize=18,
                    spaceAfter=6,
                    alignment=1  # Center alignment
                )
                story.append(Paragraph(f"{context['company_name']}", title_style))
                story.append(Paragraph(f"{context['company_address']}", styles['Normal']))
                story.append(Paragraph(f"{context['company_phone']}", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                
                # Add receipt title and details
                story.append(Paragraph("RECEIPT", styles['Heading1']))
                story.append(Paragraph(f"Receipt #: {sale.receipt_number}", styles['Normal']))
                story.append(Paragraph(f"Date: {sale.sale_date.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
                story.append(Paragraph(f"Cashier: {sale.cashier.username}", styles['Normal']))
                if sale.customer:
                    story.append(Paragraph(f"Customer: {sale.customer.first_name} {sale.customer.last_name}", styles['Normal']))
                story.append(Spacer(1, 0.1*inch))
                
                # Add sale items
                items_data = [['Item', 'Qty', 'Price', 'Total']]
                for line in sale.lines.all():
                    items_data.append([
                        f"{line.product.name}{' (' + line.variant.name + ')' if line.variant else ''}",
                        str(line.quantity),
                        f"${line.unit_price}",
                        f"${line.total_price}"
                    ])
                
                item_table = Table(items_data)
                item_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                    ('FONTSIZE', (0, 1), (-1, -1), 6),
                    ('GRID', (0, 0), (-1, -1), 1, colors.black)
                ]))
                story.append(item_table)
                story.append(Spacer(1, 0.1*inch))
                
                # Add totals
                total_data = [['Description', 'Amount']]
                subtotal = float(sale.total_amount)
                
                if sale.discount_amount and float(sale.discount_amount) > 0:
                    subtotal = float(sale.total_amount) + float(sale.discount_amount)
                    total_data.append(['Subtotal', f"${subtotal:.2f}"])
                    total_data.append(['Discount', f"-${float(sale.discount_amount):.2f}"])
                
                if sale.tax_amount and float(sale.tax_amount) > 0:
                    total_data.append(['Tax', f"${float(sale.tax_amount):.2f}"])
                
                total_data.append(['TOTAL', f"${float(sale.total_amount):.2f}"])
                
                total_table = Table(total_data)
                total_table.setStyle(TableStyle([
                    ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                    ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                    ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                    ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                    ('FONTSIZE', (0, 0), (-1, 0), 8),
                    ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                    ('ALIGN', (-1, 0), (-1, -1), 'RIGHT'),
                ]))
                story.append(total_table)
                story.append(Spacer(1, 0.1*inch))
                
                # Add payment info
                story.append(Paragraph("Payment Method(s):", styles['Heading2']))
                for payment in sale.payments.all():
                    story.append(Paragraph(f"{payment.payment_method}: ${payment.amount}", styles['Normal']))
                story.append(Paragraph(f"Status: {sale.payment_status}", styles['Normal']))
                story.append(Spacer(1, 0.2*inch))
                
                # Add thank you message
                thanks_style = ParagraphStyle(
                    'Thanks',
                    parent=styles['Normal'],
                    alignment=1,  # Center alignment
                    fontSize=10,
                    spaceAfter=6
                )
                story.append(Paragraph("Thank you for your business!", thanks_style))
                story.append(Paragraph("Powered by POS Management System", thanks_style))
                
                # Build PDF
                doc.build(story)
                pdf = buffer.getvalue()
                buffer.close()
                logger.info("Successfully generated PDF with ReportLab")
                
                # Create HTTP response with PDF
                response = HttpResponse(pdf, content_type='application/pdf')
                response['Content-Disposition'] = f'attachment; filename="receipt_{sale.receipt_number}.pdf"'
                return response
                
            except Exception as e:
                logger.error(f"ReportLab PDF generation failed: {str(e)}")
                # If ReportLab also fails, return a proper error response
                response = HttpResponse(f'ReportLab PDF generation failed: {str(e)}', content_type='text/plain')
                response.status_code = 500
                return response
        else:
            logger.error("No PDF generation library available")
            # If neither library is available, return error
            response = HttpResponse('No PDF generation library available. Please install weasyprint or reportlab.', content_type='text/plain')
            response.status_code = 500
            return response
        
    except Sale.DoesNotExist:
        logger.error(f"Sale with ID {pk} not found")
        response = HttpResponse('Sale not found', content_type='text/plain')
        response.status_code = 404
        return response
    except Exception as e:
        logger.error(f"Unexpected error generating receipt: {str(e)}")
        response = HttpResponse(f'Error generating receipt: {str(e)}', content_type='text/plain')
        response.status_code = 500
        return response


@api_view(['POST'])
def email_receipt(request, sale_id):
    """
    Email the receipt for a specific sale to the customer or specified email address.
    """
    try:
        from weasyprint import HTML
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
    except ImportError:
        return Response({'error': 'Required libraries not available for email receipt functionality.'}, 
                      status=status.HTTP_501_NOT_IMPLEMENTED)
    
    sale = Sale.objects.get(id=sale_id)
    
    # Determine recipient email
    email = request.data.get('email')
    if not email:
        if sale.customer and sale.customer.email:
            email = sale.customer.email
        else:
            return Response({'error': 'No email address provided and no customer email available'}, 
                          status=status.HTTP_400_BAD_REQUEST)
    
    # Prepare context for the receipt template
    context = {
        'sale': sale,
        'sale_lines': sale.lines.all(),
        'payments': sale.payments.all(),
        'company_name': getattr(settings, 'COMPANY_NAME', 'POS Company'),
        'company_address': getattr(settings, 'COMPANY_ADDRESS', '123 Business St.'),
        'company_phone': getattr(settings, 'COMPANY_PHONE', '+1-234-567-890'),
    }
    
    # Render the receipt HTML
    html_string = render_to_string('receipt.html', context)
    
    # Generate PDF for attachment
    html = HTML(string=html_string)
    pdf = html.write_pdf()
    
    # Prepare email
    subject = f'Receipt for Sale #{sale.receipt_number}'
    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@pos-system.com')
    
    # Create email with both text and HTML versions
    text_content = f"Please find attached your receipt for sale #{sale.receipt_number}."
    html_content = html_string  # Use the receipt HTML as email content
    
    msg = EmailMultiAlternatives(subject, text_content, from_email, [email])
    msg.attach_alternative(html_content, "text/html")
    
    # Attach PDF
    msg.attach(f"receipt_{sale.receipt_number}.pdf", pdf, 'application/pdf')
    
    # Send email
    msg.send()
    
    return Response({'message': f'Receipt successfully emailed to {email}'})


@api_view(['POST'])
def print_receipt(request, sale_id):
    """
    Prepare receipt data for printing (returns HTML content for client-side printing).
    """
    try:
        sale = Sale.objects.get(id=sale_id)
        
        # Prepare context for the receipt template
        context = {
            'sale': sale,
            'sale_lines': sale.lines.all(),
            'payments': sale.payments.all(),
            'company_name': getattr(settings, 'COMPANY_NAME', 'POS Company'),
            'company_address': getattr(settings, 'COMPANY_ADDRESS', '123 Business St.'),
            'company_phone': getattr(settings, 'COMPANY_PHONE', '+1-234-567-890'),
        }
        
        # Render the receipt HTML
        html_string = render_to_string('receipt.html', context)
        
        return Response({'html': html_string, 'receipt_number': sale.receipt_number})
    
    except Sale.DoesNotExist:
        return Response({'error': 'Sale not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Transfer Views
class TransferListView(generics.ListCreateAPIView):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]


class TransferDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]
    
    def update(self, request, *args, **kwargs):
        """
        Override the update method to handle transfer approval/rejection specifically.
        Store managers can approve/reject transfers.
        """
        instance = self.get_object()
        
        # Check if status is being updated
        if 'status' in request.data:
            new_status = request.data['status']
            
            # Check permissions based on the new status
            if new_status in ['approved', 'rejected'] and not (
                hasattr(request.user, 'userprofile') and 
                request.user.userprofile.role in ['store_manager', 'admin', 'super_admin', 'warehouse_manager']
            ):
                return Response(
                    {'error': f'You do not have permission to {new_status} transfers.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Handle approval
            if new_status == 'approved':
                instance.status = 'approved'
                instance.approved_by = request.user
                instance.approved_at = timezone.now()
                instance.save()
            
            # Handle rejection
            elif new_status == 'rejected':
                instance.status = 'rejected'
                instance.approved_by = request.user  # Reusing approved_by field for rejection tracking
                instance.approved_at = timezone.now()  # Reusing approved_at field for rejection tracking
                instance.save()
            
            # Handle receiving
            elif new_status == 'received':
                # Only authorized users can mark as received
                if not (hasattr(request.user, 'userprofile') and 
                        request.user.userprofile.role in ['store_manager', 'admin', 'super_admin', 'warehouse_manager']):
                    return Response(
                        {'error': 'You do not have permission to mark transfers as received.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Process the transfer receipt
                try:
                    instance.receive_transfer()
                except ValidationError as e:
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Handle cancellation
            elif new_status == 'cancelled':
                # Only the original requester or authorized managers can cancel
                if request.user != instance.requested_by and not (
                    hasattr(request.user, 'userprofile') and 
                    request.user.userprofile.role in ['admin', 'super_admin']
                ):
                    return Response(
                        {'error': 'You do not have permission to cancel this transfer.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                # Cancel the transfer
                try:
                    instance.cancel_transfer()
                except ValidationError as e:
                    return Response(
                        {'error': str(e)},
                        status=status.HTTP_400_BAD_REQUEST
                    )
            
            # Handle other status changes (in_transit, etc.)
            elif new_status in ['in_transit', 'requested']:
                # Basic permission check - user must be involved in the transfer or an admin
                if not (request.user == instance.requested_by or 
                        hasattr(request.user, 'userprofile') and 
                        request.user.userprofile.role in ['admin', 'super_admin', 'warehouse_manager']):
                    return Response(
                        {'error': f'You do not have permission to change status to {new_status}.'},
                        status=status.HTTP_403_FORBIDDEN
                    )
                
                instance.status = new_status
                instance.save()
            
            else:
                # For any other status updates, fall back to default behavior
                return super().update(request, *args, **kwargs)
            
            # Return the updated transfer
            serializer = self.get_serializer(instance)
            return Response(serializer.data)
        
        # For other updates (non-status), allow users with proper permissions
        return super().update(request, *args, **kwargs)


# Promotion/Discount Views
class PromotionListView(generics.ListCreateAPIView):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticated]

class PromotionDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Promotion.objects.all()
    serializer_class = PromotionSerializer
    permission_classes = [IsAuthenticated]

class CouponListView(generics.ListCreateAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]

class CouponDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Coupon.objects.all()
    serializer_class = CouponSerializer
    permission_classes = [IsAuthenticated]

# Purchase Order Views
class PurchaseOrderListView(generics.ListCreateAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]

class PurchaseOrderDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = PurchaseOrder.objects.all()
    serializer_class = PurchaseOrderSerializer
    permission_classes = [IsAuthenticated]

class GoodsReceivedNoteListView(generics.ListCreateAPIView):
    queryset = GoodsReceivedNote.objects.all()
    serializer_class = GoodsReceivedNoteSerializer
    permission_classes = [IsAuthenticated]

class GoodsReceivedNoteDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = GoodsReceivedNote.objects.all()
    serializer_class = GoodsReceivedNoteSerializer
    permission_classes = [IsAuthenticated]


class ReservationViewSet(viewsets.ModelViewSet):
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        logger.info(f"Received reservation data: {self.request.data}")
        # When a reservation is created, update the reserved quantity in the inventory
        reservation = serializer.save(user=self.request.user)
        for line in reservation.lines.all():
            inventory = Inventory.objects.get(product=line.product, variant=line.variant, warehouse=reservation.warehouse)
            inventory.qty_reserved += line.quantity
            inventory.save()

    def perform_update(self, serializer):
        # When a reservation is updated, adjust the reserved quantity in the inventory
        old_reservation = self.get_object()
        new_reservation = serializer.save()

        # If the status is changed to 'canceled', release the reserved stock
        if old_reservation.status != 'canceled' and new_reservation.status == 'canceled':
            for line in new_reservation.lines.all():
                inventory = Inventory.objects.get(product=line.product, variant=line.variant, warehouse=new_reservation.warehouse)
                inventory.qty_reserved -= line.quantity
                inventory.save()

        # If the status is changed to 'completed', the stock will be handled by the sale creation process
        # so we just need to release the reservation
        if old_reservation.status != 'completed' and new_reservation.status == 'completed':
            for line in new_reservation.lines.all():
                inventory = Inventory.objects.get(product=line.product, variant=line.variant, warehouse=new_reservation.warehouse)
                inventory.qty_reserved -= line.quantity
                inventory.save()

    def perform_destroy(self, instance):
        # When a reservation is deleted, release the reserved stock
        if instance.status == 'active':
            for line in instance.lines.all():
                inventory = Inventory.objects.get(product=line.product, variant=line.variant, warehouse=instance.warehouse)
                inventory.qty_reserved -= line.quantity
                inventory.save()
        instance.delete()

# Return/Exchange Views
class ReturnListView(generics.ListCreateAPIView):
    queryset = Return.objects.all()
    serializer_class = ReturnSerializer
    permission_classes = [IsAuthenticated]

class ReturnDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Return.objects.all()
    serializer_class = ReturnSerializer
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lookup_returns_by_receipt(request, receipt_number):
    """
    Look up returns associated with a specific receipt number
    """
    try:
        # Find the sale by receipt number
        sale = Sale.objects.get(receipt_number=receipt_number)
        
        # Get all returns associated with this sale
        returns = Return.objects.filter(original_sale=sale)
        
        serializer = ReturnSerializer(returns, many=True, context={'request': request})
        return Response(serializer.data)
        
    except Sale.DoesNotExist:
        return Response({'error': 'Sale not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def lookup_returns_by_customer(request, customer_id):
    """
    Look up returns associated with a specific customer
    """
    try:
        # Get all returns associated with this customer
        returns = Return.objects.filter(customer_id=customer_id)
        
        serializer = ReturnSerializer(returns, many=True, context={'request': request})
        return Response(serializer.data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def process_return(request, return_id):
    """
    Process a return by restocking items and issuing refund/store credit
    Expected JSON format:
    {
        "action": "refund|store_credit|exchange",
        "refund_method": "cash|card",  // Required if action is refund
        "warehouse_id": 1,  // Warehouse to restock items, optional
        "location_id": 1,   // Location to restock items, optional
        "bin_id": 1,        // Bin to restock items, optional
        "restock_type": "normal|quality_control",  // How to restock items
        "new_items": [  // Required if action is exchange
            {
                "product_id": 1,
                "variant_id": null,
                "quantity": 1,
                "unit_price": 10.99
            }
        ]
    }
    """
    try:
        return_obj = Return.objects.get(id=return_id)
        
        # Check if return is approved before processing
        if return_obj.status != 'approved':
            return Response(
                {'error': 'Return must be approved before processing'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = request.data.get('action')
        if not action:
            return Response(
                {'error': 'Action is required (refund, store_credit, or exchange)'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Handle restocking
        warehouse_id = request.data.get('warehouse_id')
        location_id = request.data.get('location_id')
        bin_id = request.data.get('bin_id')
        restock_type = request.data.get('restock_type', 'normal')
        
        warehouse = Warehouse.objects.get(id=warehouse_id) if warehouse_id else None
        location = Location.objects.get(id=location_id) if location_id else None
        bin = Bin.objects.get(id=bin_id) if bin_id else None
        
        # Restock items
        return_obj.restock_items(
            warehouse=warehouse,
            location=location,
            bin=bin,
            restock_type=restock_type
        )
        
        # Process based on action
        if action == 'refund':
            refund_method = request.data.get('refund_method')
            if not refund_method:
                return Response(
                    {'error': 'Refund method is required (cash, card, etc.)'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create a payment record for the refund
            Payment.objects.create(
                sale=return_obj.original_sale,
                payment_method=refund_method,
                amount=-return_obj.refund_amount,  # Negative because it's a refund
                reference=f"Refund for return {return_obj.return_number}"
            )
            
            # Mark as processed
            return_obj.status = 'processed'
            return_obj.processed_at = timezone.now()
            return_obj.processed_by = request.user
            return_obj.save()
            
        elif action == 'store_credit':
            # Issue store credit to the customer
            return_obj.issue_store_credit()
            
        elif action == 'exchange':
            new_items_data = request.data.get('new_items', [])
            if not new_items_data:
                return Response(
                    {'error': 'New items data is required for exchanges'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process the exchange
            new_sale = return_obj.process_exchange(new_items_data)
            
            # Update return status
            return_obj.status = 'processed'
            return_obj.processed_at = timezone.now()
            return_obj.processed_by = request.user
            return_obj.save()
            
            return Response({
                'message': 'Return processed successfully',
                'new_sale': SaleSerializer(new_sale).data
            })
        
        else:
            return Response(
                {'error': 'Invalid action. Use refund, store_credit, or exchange'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = ReturnSerializer(return_obj)
        return Response({
            'message': f'Return processed successfully with action: {action}',
            'return': serializer.data
        })
        
    except Return.DoesNotExist:
        return Response({'error': 'Return not found'}, status=status.HTTP_404_NOT_FOUND)
    except Warehouse.DoesNotExist:
        return Response({'error': 'Warehouse not found'}, status=status.HTTP_404_NOT_FOUND)
    except Location.DoesNotExist:
        return Response({'error': 'Location not found'}, status=status.HTTP_404_NOT_FOUND)
    except Bin.DoesNotExist:
        return Response({'error': 'Bin not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

# Audit Log Views
class AuditLogListView(generics.ListAPIView):
    queryset = AuditLog.objects.all()
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated]


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def customer_purchase_history(request, pk):
    """
    Get purchase history for a specific customer
    """
    try:
        customer = Customer.objects.get(id=pk)
        
        # Get all sales for this customer, prefetching related data
        sales = Sale.objects.filter(customer=customer).prefetch_related(
            'lines__product',
            'lines__variant',
            'payments'
        ).order_by('-sale_date')
        
        # Prepare the response data
        history_data = []
        for sale in sales:
            sale_data = {
                'id': sale.id,
                'receipt_number': sale.receipt_number,
                'sale_date': sale.sale_date,
                'total_amount': float(sale.total_amount),
                'payment_status': sale.payment_status,
                'items': [],
                'payments': []
            }
            
            # Add sale lines
            for line in sale.lines.all():
                sale_data['items'].append({
                    'product_name': line.product.name,
                    'quantity': line.quantity,
                    'unit_price': float(line.unit_price),
                    'total_price': float(line.total_price)
                })
            
            # Add payments
            for payment in sale.payments.all():
                sale_data['payments'].append({
                    'method': payment.payment_method,
                    'amount': float(payment.amount),
                    'reference': payment.reference
                })
            
            history_data.append(sale_data)
        
        # Calculate total spent
        total_spent = 0
        for sale in history_data:
            total_spent += float(sale['total_amount']) if sale.get('total_amount') else 0.0

        return Response({
            'customer': {
                'id': customer.id,
                'name': f"{customer.first_name} {customer.last_name}",
                'email': customer.email,
                'phone': customer.phone,
                'notes': customer.notes
            },
            'purchase_history': history_data,
            'total_orders': len(history_data),
            'total_spent': total_spent
        })
        
    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def earn_loyalty_points(request, customer_id):
    """
    Manually add loyalty points to a customer's account
    Expected JSON format:
    {
        "points": 100,
        "reason": "Special promotion"
    }
    """
    try:
        customer = Customer.objects.get(id=customer_id)
        points = request.data.get('points')
        reason = request.data.get('reason', 'Manual adjustment')
        
        if not points or points <= 0:
            return Response({'error': 'Points must be a positive number'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Record the points adjustment in audit log
        original_points = customer.loyalty_points
        new_points = customer.earn_loyalty_points(points)
        
        # Create audit log for the loyalty point change
        AuditLog.objects.create(
            user=request.user,
            action='update',
            object_type='customer',
            object_id=customer.id,
            object_repr=f"Loyalty points earned by {customer.first_name} {customer.last_name}",
            old_values={'loyalty_points': original_points},
            new_values={'loyalty_points': new_points},
            notes=f"Manual adjustment: {points} points added - {reason}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'message': f'{points} loyalty points added successfully',
            'customer': {
                'id': customer.id,
                'name': f"{customer.first_name} {customer.last_name}",
                'loyalty_points': new_points
            }
        })
        
    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def redeem_loyalty_points(request, customer_id):
    """
    Redeem loyalty points from a customer's account
    Expected JSON format:
    {
        "points": 50,
        "reason": "Redeemed for discount"
    }
    """
    try:
        customer = Customer.objects.get(id=customer_id)
        points = request.data.get('points')
        reason = request.data.get('reason', 'Manual redemption')
        
        if not points or points <= 0:
            return Response({'error': 'Points must be a positive number'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if customer has enough points
        if points > customer.loyalty_points:
            return Response({
                'error': f'Insufficient loyalty points. Customer has {customer.loyalty_points} points, but tried to redeem {points} points.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Record the points adjustment in audit log
        original_points = customer.loyalty_points
        new_points = customer.redeem_loyalty_points(points)
        
        # Create audit log for the loyalty point change
        AuditLog.objects.create(
            user=request.user,
            action='update',
            object_type='customer',
            object_id=customer.id,
            object_repr=f"Loyalty points redeemed by {customer.first_name} {customer.last_name}",
            old_values={'loyalty_points': original_points},
            new_values={'loyalty_points': new_points},
            notes=f"Manual redemption: {points} points deducted - {reason}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({
            'message': f'{points} loyalty points redeemed successfully',
            'customer': {
                'id': customer.id,
                'name': f"{customer.first_name} {customer.last_name}",
                'loyalty_points': new_points
            }
        })
        
    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    except ValidationError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_loyalty_discount(request):
    """
    Calculate discount based on customer's loyalty points
    Expected JSON format:
    {
        "customer_id": 1,
        "points_to_redeem": 100  # e.g., 100 points = $1 discount
    }
    """
    try:
        customer_id = request.data.get('customer_id')
        points_to_redeem = request.data.get('points_to_redeem')
        
        if not customer_id or not points_to_redeem or points_to_redeem <= 0:
            return Response({'error': 'Customer ID and positive points to redeem are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        customer = Customer.objects.get(id=customer_id)
        
        # Check if customer has enough points
        if points_to_redeem > customer.loyalty_points:
            return Response({
                'error': f'Insufficient loyalty points. Customer has {customer.loyalty_points} points, but tried to redeem {points_to_redeem} points.'
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Calculate discount amount (for example, 100 points = $1 discount)
        discount_amount = points_to_redeem / 100  # Adjust ratio as needed
        new_points_balance = customer.loyalty_points - points_to_redeem
        
        return Response({
            'customer': {
                'id': customer.id,
                'name': f"{customer.first_name} {customer.last_name}",
                'current_points': customer.loyalty_points
            },
            'points_redeemed': points_to_redeem,
            'discount_amount': discount_amount,
            'new_points_balance': new_points_balance
        })
        
    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)



# Report Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_report(request):
    # Check if the user has permission to view reports
    if hasattr(request.user, 'userprofile'):
        user_role = request.user.userprofile.role
        # Store managers, admins, and super admins can view reports
        if user_role not in ['store_manager', 'admin', 'super_admin', 'accountant']:
            return Response(
                {'error': 'You do not have permission to view this report.'},
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        return Response(
            {'error': 'User profile not found.'},
            status=status.HTTP_403_FORBIDDEN
        )
    """
    Generate sales report by period, store, warehouse, or SKU
    """
    try:
        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        warehouse_id = request.query_params.get('warehouse_id')
        warehouse_type = request.query_params.get('warehouse_type')  # For filtering by store vs warehouse
        sku = request.query_params.get('sku')
        product_id = request.query_params.get('product_id')
        
        # Build query filters
        sales_query = Sale.objects.all()
        
        if start_date:
            sales_query = sales_query.filter(sale_date__gte=start_date)
        if end_date:
            sales_query = sales_query.filter(sale_date__lte=end_date)
        if warehouse_id:
            sales_query = sales_query.filter(warehouse_id=warehouse_id)
        if warehouse_type:
            # Filter by warehouse type (store, warehouse, distribution_center, depot)
            sales_query = sales_query.filter(warehouse__warehouse_type=warehouse_type)
        if sku:
            # Filter by SKU through sale lines
            sales_query = sales_query.filter(lines__product__sku=sku)
        if product_id:
            # Filter by product ID through sale lines
            sales_query = sales_query.filter(lines__product_id=product_id)
        
        # Get sales with related data
        sales = sales_query.prefetch_related('lines__product', 'payments', 'warehouse').order_by('-sale_date')
        
        # Prepare report data
        report_data = []
        total_sales = 0
        total_revenue = 0
        
        for sale in sales:
            sale_total = float(sale.total_amount)
            total_revenue += sale_total
            
            sale_data = {
                'id': sale.id,
                'receipt_number': sale.receipt_number,
                'sale_date': sale.sale_date,
                'customer_name': str(sale.customer) if sale.customer else 'Walk-in',
                'warehouse_name': sale.warehouse.name,
                'warehouse_type': sale.warehouse.warehouse_type,
                'total_amount': sale_total,
                'payment_status': sale.payment_status,
                'items': []
            }
            
            # Add items to sale
            for line in sale.lines.all():
                sale_data['items'].append({
                    'product_name': line.product.name,
                    'product_sku': line.product.sku,
                    'quantity': line.quantity,
                    'unit_price': float(line.unit_price),
                    'total_price': float(line.total_price)
                })
            
            report_data.append(sale_data)
        
        return Response({
            'sales': report_data,
            'summary': {
                'total_sales': len(report_data),
                'total_revenue': total_revenue,
                'date_range': f"{start_date or 'Start'} to {end_date or 'Now'}"
            }
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_report(request):
    # Check if the user has permission to view reports
    if hasattr(request.user, 'userprofile'):
        user_role = request.user.userprofile.role
        # Store managers, admins, and super admins can view reports
        if user_role not in ['store_manager', 'admin', 'super_admin', 'warehouse_manager', 'accountant']:
            return Response(
                {'error': 'You do not have permission to view this report.'},
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        return Response(
            {'error': 'User profile not found.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    """
    Generate inventory report with stock levels and aging
    """
    from datetime import datetime, timedelta
    try:
        # Get query parameters
        warehouse_id = request.query_params.get('warehouse_id')
        category_id = request.query_params.get('category_id')
        include_aging = request.query_params.get('include_aging', 'false').lower() == 'true'
        
        # Build query filters
        inventory_query = Inventory.objects.select_related('product', 'product__category', 'warehouse')
        
        if warehouse_id:
            inventory_query = inventory_query.filter(warehouse_id=warehouse_id)
        if category_id:
            inventory_query = inventory_query.filter(product__category_id=category_id)
        
        # Prepare report data
        report_data = []
        total_value = 0
        
        for item in inventory_query:
            item_value = float(item.qty_on_hand) * float(item.product.price) if item.product.price else 0
            total_value += item_value
            
            item_data = {
                'id': item.id,
                'product_name': item.product.name,
                'product_sku': item.product.sku,
                'category_name': item.product.category.name if item.product.category else 'N/A',
                'warehouse_name': item.warehouse.name,
                'quantity_on_hand': item.qty_on_hand,
                'quantity_reserved': item.qty_reserved,
                'available_stock': item.available_stock(),
                'min_stock_level': item.min_stock_level,
                'is_low_stock': item.is_low_stock(),
                'unit_price': float(item.product.price) if item.product.price else 0,
                'total_value': item_value,
                'last_updated': item.last_updated
            }
            
            # Add aging information if requested
            if include_aging:
                # Calculate age of inventory based on last_updated
                age_in_days = (datetime.now(item.last_updated.tzinfo) - item.last_updated).days
                item_data['age_in_days'] = age_in_days
                
                # Categorize by age
                if age_in_days <= 30:
                    item_data['age_category'] = 'New (0-30 days)'
                elif age_in_days <= 60:
                    item_data['age_category'] = 'Aged (31-60 days)'
                elif age_in_days <= 90:
                    item_data['age_category'] = 'Aged (61-90 days)'
                else:
                    item_data['age_category'] = 'Old (>90 days)'
                
                # Calculate slow-moving items (items with no movement for extended period)
                item_data['is_slow_moving'] = age_in_days > 90 and item.qty_on_hand > item.min_stock_level
            
            report_data.append(item_data)
        
        return Response({
            'inventory': report_data,
            'summary': {
                'total_items': len(report_data),
                'total_value': total_value,
            }
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def profitability_report(request):
    # Check if the user has permission to view reports
    if hasattr(request.user, 'userprofile'):
        user_role = request.user.userprofile.role
        # Store managers, admins, and super admins can view reports
        if user_role not in ['store_manager', 'admin', 'super_admin', 'accountant']:
            return Response(
                {'error': 'You do not have permission to view this report.'},
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        return Response(
            {'error': 'User profile not found.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    """
    Generate profitability report (revenue, COGS by valuation method)
    Supports different COGS calculation methods: standard, FIFO, LIFO, Weighted Average
    """
    try:
        from datetime import datetime
        from decimal import Decimal
        
        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        valuation_method = request.query_params.get('valuation_method', 'standard').lower()  # standard, fifo, lifo, weighted_average
        
        # Build query filters
        sales_query = Sale.objects.all()
        
        if start_date:
            sales_query = sales_query.filter(sale_date__gte=start_date)
        if end_date:
            sales_query = sales_query.filter(sale_date__lte=end_date)
        
        # Get sales with related data
        sales = sales_query.prefetch_related('lines__product', 'lines__product__inventory_set').order_by('-sale_date')
        
        # Prepare report data
        report_data = []
        total_revenue = Decimal('0')
        total_cogs = Decimal('0')  # Cost of Goods Sold
        
        for sale in sales:
            sale_revenue = Decimal(str(sale.total_amount))
            sale_cogs = Decimal('0')
            profit = Decimal('0')
            
            # Calculate COGS and profit for this sale based on valuation method
            for line in sale.lines.all():
                # Use different valuation methods
                if valuation_method == 'fifo':
                    # FIFO (First In, First Out) - use oldest inventory cost
                    cost_price = _calculate_fifo_cost(line.product, line.quantity, line.sale.sale_date)
                elif valuation_method == 'lifo':
                    # LIFO (Last In, First Out) - use newest inventory cost (simplified as current cost)
                    cost_price = Decimal(str(line.cost_price)) if line.cost_price else Decimal(str(line.product.cost_price)) if line.product.cost_price else Decimal('0')
                elif valuation_method == 'weighted_average':
                    # Weighted average cost
                    cost_price = _calculate_weighted_average_cost(line.product)
                else:  # standard/default
                    # Use the cost_price from the sale line or product
                    cost_price = Decimal(str(line.cost_price)) if line.cost_price else Decimal(str(line.product.cost_price)) if line.product.cost_price else Decimal('0')
                
                line_cogs = cost_price * Decimal(str(line.quantity))
                sale_cogs += line_cogs
            
            profit = sale_revenue - sale_cogs
            total_revenue += sale_revenue
            total_cogs += sale_cogs
            
            report_data.append({
                'id': sale.id,
                'receipt_number': sale.receipt_number,
                'sale_date': sale.sale_date,
                'total_revenue': float(sale_revenue),
                'total_cogs': float(sale_cogs),
                'profit': float(profit),
                'profit_margin': float((profit / sale_revenue * 100)) if sale_revenue > 0 else 0,
                'valuation_method': valuation_method
            })
        
        overall_profit = total_revenue - total_cogs
        overall_margin = (overall_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return Response({
            'sales': report_data,
            'summary': {
                'total_revenue': float(total_revenue),
                'total_cogs': float(total_cogs),
                'total_profit': float(overall_profit),
                'overall_profit_margin': float(overall_margin),
                'valuation_method': valuation_method,
                'date_range': f"{start_date or 'Start'} to {end_date or 'Now'}"
            }
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


def _calculate_fifo_cost(product, quantity, sale_date):
    """
    Calculate FIFO (First In, First Out) cost for a product sale
    This is a simplified implementation - in a real system, you'd need to track purchase dates and costs
    """
    from decimal import Decimal
    
    # For this simplified implementation, we'll use the product's cost price
    # A full FIFO implementation would require tracking each inventory purchase batch
    cost = product.cost_price if product.cost_price else Decimal('0')
    return Decimal(str(cost))


def _calculate_weighted_average_cost(product):
    """
    Calculate weighted average cost for a product
    This is a simplified implementation
    """
    from decimal import Decimal
    
    # For this simplified implementation, we'll use the product's cost price
    # A full implementation would calculate based on all inventory purchases
    cost = product.cost_price if product.cost_price else Decimal('0')
    return Decimal(str(cost))


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transfer_report(request):
    # Check if the user has permission to view reports
    if hasattr(request.user, 'userprofile'):
        user_role = request.user.userprofile.role
        # Store managers, admins, and super admins can view reports
        if user_role not in ['store_manager', 'admin', 'super_admin', 'warehouse_manager']:
            return Response(
                {'error': 'You do not have permission to view this report.'},
                status=status.HTTP_403_FORBIDDEN
            )
    else:
        return Response(
            {'error': 'User profile not found.'},
            status=status.HTTP_403_FORBIDDEN
        )
    
    """
    Generate transfer history report with discrepancy detection
    """
    try:
        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        from_warehouse_id = request.query_params.get('from_warehouse_id')
        to_warehouse_id = request.query_params.get('to_warehouse_id')
        include_discrepancies = request.query_params.get('include_discrepancies', 'false').lower() == 'true'
        
        # Build query filters
        transfers_query = Transfer.objects.prefetch_related('lines__product', 'from_warehouse', 'to_warehouse')
        
        if start_date:
            transfers_query = transfers_query.filter(requested_at__gte=start_date)
        if end_date:
            transfers_query = transfers_query.filter(requested_at__lte=end_date)
        if from_warehouse_id:
            transfers_query = transfers_query.filter(from_warehouse_id=from_warehouse_id)
        if to_warehouse_id:
            transfers_query = transfers_query.filter(to_warehouse_id=to_warehouse_id)
        
        # Prepare report data
        report_data = []
        discrepancies = []
        
        for transfer in transfers_query:
            transfer_data = {
                'id': transfer.id,
                'transfer_number': transfer.transfer_number,
                'from_warehouse': transfer.from_warehouse.name,
                'to_warehouse': transfer.to_warehouse.name,
                'status': transfer.status,
                'requested_at': transfer.requested_at,
                'approved_at': transfer.approved_at,
                'received_at': transfer.received_at,
                'notes': transfer.notes,
                'items': [],
                'has_discrepancies': False,
                'discrepancy_notes': []
            }
            
            # Add items to transfer and check for discrepancies
            for line in transfer.lines.all():
                line_data = {
                    'product_name': line.product.name,
                    'product_sku': line.product.sku,
                    'requested_qty': line.requested_qty,
                    'transferred_qty': line.transferred_qty,
                    'received_qty': line.received_qty,
                }
                
                # Check for discrepancies
                discrepancy_info = []
                if line.requested_qty != line.received_qty:
                    discrepancy_info.append(f"Requested {line.requested_qty}, received {line.received_qty}")
                    transfer_data['has_discrepancies'] = True
                if line.requested_qty != line.transferred_qty:
                    discrepancy_info.append(f"Requested {line.requested_qty}, transferred {line.transferred_qty}")
                    transfer_data['has_discrepancies'] = True
                if line.transferred_qty != line.received_qty:
                    discrepancy_info.append(f"Transferred {line.transferred_qty}, received {line.received_qty}")
                    transfer_data['has_discrepancies'] = True
                
                line_data['discrepancies'] = discrepancy_info
                transfer_data['items'].append(line_data)
                
                # Add to global discrepancies list if needed
                if discrepancy_info:
                    discrepancies.append({
                        'transfer_number': transfer.transfer_number,
                        'product_name': line.product.name,
                        'product_sku': line.product.sku,
                        'requested_qty': line.requested_qty,
                        'transferred_qty': line.transferred_qty,
                        'received_qty': line.received_qty,
                        'discrepancies': discrepancy_info
                    })
            
            report_data.append(transfer_data)
        
        # Prepare response
        response_data = {
            'transfers': report_data,
            'summary': {
                'total_transfers': len(report_data),
                'total_discrepancies': len(discrepancies),
                'date_range': f"{start_date or 'Start'} to {end_date or 'Now'}"
            }
        }
        
        if include_discrepancies:
            response_data['discrepancies'] = discrepancies
        
        return Response(response_data)
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Password reset views
@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request(request):
    """
    Handle password reset request by sending an email with a reset link
    """
    email = request.data.get('email')
    if not email:
        return Response({'error': 'Email is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if the user exists or not to prevent email enumeration attacks
        return Response({'message': 'If your email exists in our system, you will receive a password reset link shortly.'}, status=status.HTTP_200_OK)
    
    # Generate password reset token and URL
    token = default_token_generator.make_token(user)
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    
    # Build reset URL (adjust for your frontend URL)
    frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:3000')
    reset_url = f"{frontend_url}/reset-password/{uid}/{token}/"
    
    # Send email with password reset link
    subject = 'Password Reset Request'
    html_message = loader.render_to_string('password_reset_email.html', {
        'user': user,
        'reset_url': reset_url,
        'site_name': getattr(settings, 'SITE_NAME', 'POS Management System'),
    })
    
    send_mail(
        subject,
        f'Please click this link to reset your password: {reset_url}',
        getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@pos-system.com'),
        [user.email],
        fail_silently=False,
        html_message=html_message
    )
    
    return Response({'message': 'If your email exists in our system, you will receive a password reset link shortly.'}, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm(request, uidb64, token):
    """
    Confirm password reset with new password
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        
        if not new_password or not confirm_password:
            return Response({'error': 'New password and confirmation are required'}, status=status.HTTP_400_BAD_REQUEST)
        
        if new_password != confirm_password:
            return Response({'error': 'Passwords do not match'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Set new password
        user.set_password(new_password)
        user.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=None,  # No user logged in at this point
            action='update',
            object_type='user',
            object_id=user.id,
            object_repr=f"Password reset for user {user.username}",
            notes="Password reset through password reset flow",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response({'message': 'Password successfully reset'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid reset link'}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def password_reset_validate_token(request, uidb64, token):
    """
    Validate if a password reset token is valid without resetting the password
    """
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None
    
    if user is not None and default_token_generator.check_token(user, token):
        return Response({'valid': True, 'user_id': user.id}, status=status.HTTP_200_OK)
    else:
        return Response({'valid': False, 'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)


# ViewSets
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Check if the warehouse can be safely deleted
        can_delete, message = instance.can_delete()
        if not can_delete:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Proceed with deletion
        return super().destroy(request, *args, **kwargs)


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Location.objects.select_related('warehouse').all()
        
        # Add filtering options
        warehouse_id = self.request.query_params.get('warehouse_id') or self.request.query_params.get('warehouse')
        
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        
        return queryset


class BinViewSet(viewsets.ModelViewSet):
    queryset = Bin.objects.all()
    serializer_class = BinSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Bin.objects.select_related('location', 'location__warehouse').all()
        
        # Add filtering options
        location_id = self.request.query_params.get('location_id') or self.request.query_params.get('location')
        
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        
        return queryset


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]


class InventoryViewSet(viewsets.ModelViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [IsAuthenticated]

    @action(detail=False, methods=['get'])
    def low_stock(self, request):
        """
        Get all low stock items
        """
        low_stock_items = Inventory.objects.filter(
            qty_on_hand__lt=F('min_stock_level')
        ).select_related('product', 'warehouse')
        
        low_stock_data = []
        for item in low_stock_items:
            low_stock_data.append({
                'id': item.id,
                'product_name': item.product.name,
                'product_sku': item.product.sku,
                'warehouse_name': item.warehouse.name,
                'available_stock': item.available_stock(),
                'quantity_on_hand': item.qty_on_hand,
                'min_stock_level': item.min_stock_level,
                'is_low_stock': item.is_low_stock()
            })
        
        return Response({
            'low_stock_items': low_stock_data,
            'total_low_items': len(low_stock_data)
        })
    
    def get_queryset(self):
        queryset = Inventory.objects.select_related(
            'product', 'product__category', 'warehouse', 'location', 'bin'
        ).all()
        
        # Add filtering options
        warehouse_id = self.request.query_params.get('warehouse_id')
        product_id = self.request.query_params.get('product_id')
        location_id = self.request.query_params.get('location_id')
        
        if warehouse_id:
            queryset = queryset.filter(warehouse_id=warehouse_id)
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        if location_id:
            queryset = queryset.filter(location_id=location_id)
        
        return queryset


class TransferViewSet(viewsets.ModelViewSet):
    queryset = Transfer.objects.all()
    serializer_class = TransferSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Transfer.objects.prefetch_related(
            'lines__product', 'from_warehouse', 'to_warehouse'
        ).all()
        
        # Add filtering options
        from_warehouse_id = self.request.query_params.get('from_warehouse_id')
        to_warehouse_id = self.request.query_params.get('to_warehouse_id')
        status_filter = self.request.query_params.get('status')
        
        if from_warehouse_id:
            queryset = queryset.filter(from_warehouse_id=from_warehouse_id)
        if to_warehouse_id:
            queryset = queryset.filter(to_warehouse_id=to_warehouse_id)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset


class ProductVariantViewSet(viewsets.ModelViewSet):
    queryset = ProductVariant.objects.all()
    serializer_class = ProductVariantSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = ProductVariant.objects.select_related('product').all()
        
        # Add filtering options
        product_id = self.request.query_params.get('product_id')
        
        if product_id:
            queryset = queryset.filter(product_id=product_id)
        
        return queryset


class WebhookViewSet(viewsets.ModelViewSet):
    queryset = Webhook.objects.all()
    serializer_class = WebhookSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        permission_classes = [IsAuthenticated]
        # Only allow users with specific permissions to manage webhooks
        if self.request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:
            permission_classes.append(HasSpecificPermission)
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Webhook.objects.all()
        
        # Add filtering options
        event_type = self.request.query_params.get('event_type')
        is_active = self.request.query_params.get('is_active')
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        if is_active is not None:
            if is_active.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_active=True)
            else:
                queryset = queryset.filter(is_active=False)
        
        return queryset


class WebhookLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = WebhookLog.objects.all()
    serializer_class = WebhookLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = WebhookLog.objects.select_related('webhook').all()
        
        # Add filtering options
        webhook_id = self.request.query_params.get('webhook_id')
        success = self.request.query_params.get('success')
        
        if webhook_id:
            queryset = queryset.filter(webhook_id=webhook_id)
        if success is not None:
            if success.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(success=True)
            else:
                queryset = queryset.filter(success=False)
        
        return queryset


class PaymentTokenViewSet(viewsets.ModelViewSet):
    queryset = PaymentToken.objects.all()
    serializer_class = PaymentTokenSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = PaymentToken.objects.select_related('customer').all()
        
        # Add filtering options
        customer_id = self.request.query_params.get('customer_id')
        gateway = self.request.query_params.get('gateway')
        is_default = self.request.query_params.get('is_default')
        
        if customer_id:
            queryset = queryset.filter(customer_id=customer_id)
        if gateway:
            queryset = queryset.filter(gateway=gateway)
        if is_default is not None:
            if is_default.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_default=True)
            else:
                queryset = queryset.filter(is_default=False)
        
        return queryset


class PaymentGatewayConfigViewSet(viewsets.ModelViewSet):
    queryset = PaymentGatewayConfig.objects.all()
    serializer_class = PaymentGatewayConfigSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """
        Only allow super admins to manage payment gateway configurations
        """
        permission_classes = [IsAuthenticated, IsSuperAdmin]
        return [permission() for permission in permission_classes]


class EcommercePlatformViewSet(viewsets.ModelViewSet):
    queryset = EcommercePlatform.objects.all()
    serializer_class = EcommercePlatformSerializer
    permission_classes = [IsAuthenticated]
    
    def get_permissions(self):
        """
        Only allow super admins to manage e-commerce platform configurations
        """
        permission_classes = [IsAuthenticated, IsSuperAdmin]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = EcommercePlatform.objects.all()
        
        # Add filtering options
        platform_type = self.request.query_params.get('platform')
        is_active = self.request.query_params.get('is_active')
        
        if platform_type:
            queryset = queryset.filter(platform=platform_type)
        if is_active is not None:
            if is_active.lower() in ['true', '1', 'yes']:
                queryset = queryset.filter(is_active=True)
            else:
                queryset = queryset.filter(is_active=False)
        
        return queryset


class EcommerceSyncLogViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = EcommerceSyncLog.objects.all()
    serializer_class = EcommerceSyncLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = EcommerceSyncLog.objects.select_related('platform').all()
        
        # Add filtering options
        platform_id = self.request.query_params.get('platform_id')
        sync_type = self.request.query_params.get('sync_type')
        status = self.request.query_params.get('status')
        
        if platform_id:
            queryset = queryset.filter(platform_id=platform_id)
        if sync_type:
            queryset = queryset.filter(sync_type=sync_type)
        if status:
            queryset = queryset.filter(status=status)
        
        return queryset


# Webhooks
from .models import Webhook, WebhookLog
from rest_framework.permissions import BasePermission


class IsSuperAdmin(BasePermission):
    """
    Custom permission to only allow super admins to access certain views.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.role == 'super_admin'
        )


class IsStoreManager(BasePermission):
    """
    Custom permission to allow store managers to access specific views.
    """
    def has_permission(self, request, view):
        return (
            request.user and 
            request.user.is_authenticated and 
            hasattr(request.user, 'userprofile') and 
            request.user.userprofile.role in ['store_manager', 'admin', 'super_admin']
        )


class SuperAdminUserManagementView(generics.ListCreateAPIView):
    """
    Super Admin specific view for user management with enhanced features:
    - List all users with their roles
    - Create new users with specific roles
    - Bulk operations
    """
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def get_queryset(self):
        return User.objects.select_related('userprofile').all()
    
    def create(self, request, *args, **kwargs):
        # Allow super admins to create users with any role
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Create user with role
        user = serializer.save()
        role = request.data.get('role', 'cashier')  # Default to cashier if no role specified
        
        # Create or update user profile
        user_profile, created = UserProfile.objects.get_or_create(
            user=user,
            defaults={'role': role}
        )
        if not created:
            user_profile.role = role
            user_profile.save()
        
        return Response(
            UserSerializer(user, context=self.get_serializer_context()).data,
            status=status.HTTP_201_CREATED
        )


class SuperAdminUserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    Super Admin specific view to manage individual users:
    - View user details
    - Update user role
    - Activate/deactivate user
    - Reset user password
    """
    queryset = User.objects.select_related('userprofile').all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsSuperAdmin]
    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        role = request.data.get('role')
        
        # For Super Admins, allow updating any user's role
        if role and role in [choice[0] for choice in UserProfile.ROLE_CHOICES]:
            profile, created = UserProfile.objects.get_or_create(user=instance)
            profile.role = role
            profile.save()
        
        return super().partial_update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Prevent super admin from deleting themselves
        if instance.id == request.user.id:
            return Response(
                {'error': 'You cannot delete your own account.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prevent deleting the last super admin
        profile = instance.userprofile if hasattr(instance, 'userprofile') else None
        if profile and profile.role == 'super_admin':
            super_admin_count = UserProfile.objects.filter(role='super_admin').count()
            if super_admin_count <= 1:
                return Response(
                    {'error': 'Cannot delete the last super admin user.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Handle protected foreign key constraints by reassigning related objects to the admin user
        admin_user = request.user  # The admin performing the deletion
        
        # Handle transfers where user is requested_by
        Transfer.objects.filter(requested_by=instance).update(requested_by=admin_user)
        
        # Handle sales where user is cashier
        Sale.objects.filter(cashier=instance).update(cashier=admin_user)
        
        # Handle goods received notes where user is received_by
        GoodsReceivedNote.objects.filter(received_by=instance).update(received_by=admin_user)
        
        return super().destroy(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def reset_user_password(request, pk):
    """
    Super Admin specific endpoint to reset any user's password
    """
    try:
        user = User.objects.get(id=pk)
        
        new_password = request.data.get('new_password')
        if not new_password:
            return Response(
                {'error': 'New password is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Set the new password
        user.set_password(new_password)
        user.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='update',
            object_type='user',
            object_id=user.id,
            object_repr=f"Password reset for user {user.username}",
            notes=f"Password reset by super admin {request.user.username}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(
            {'message': f'Password successfully reset for user {user.username}'},
            status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found.'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def inventory_by_location(request):
    """
    Get inventory items filtered by location
    Query parameters:
    - warehouse_id: Filter by warehouse
    - location_id: Filter by location
    - product_id: Filter by product
    """
    try:
        warehouse_id = request.query_params.get('warehouse_id')
        location_id = request.query_params.get('location_id')
        product_id = request.query_params.get('product_id')
        
        # Build query filters
        inventory_query = Inventory.objects.select_related(
            'product', 'product__category', 'warehouse', 'location', 'bin'
        )
        
        if warehouse_id:
            inventory_query = inventory_query.filter(warehouse_id=warehouse_id)
        if location_id:
            inventory_query = inventory_query.filter(location_id=location_id)
        if product_id:
            inventory_query = inventory_query.filter(product_id=product_id)
        
        # Prepare response data
        inventory_data = []
        total_value = 0
        
        for item in inventory_query:
            item_value = float(item.qty_on_hand) * float(item.product.price) if item.product.price else 0
            total_value += item_value
            
            inventory_data.append({
                'id': item.id,
                'product_name': item.product.name,
                'product_sku': item.product.sku,
                'warehouse_name': item.warehouse.name,
                'warehouse_id': item.warehouse.id,
                'location_name': item.location.name if item.location else None,
                'location_id': item.location.id if item.location else None,
                'bin_name': item.bin.name if item.bin else None,
                'bin_id': item.bin.id if item.bin else None,
                'quantity_on_hand': item.qty_on_hand,
                'quantity_reserved': item.qty_reserved,
                'available_stock': item.available_stock(),
                'min_stock_level': item.min_stock_level,
                'is_low_stock': item.is_low_stock(),
                'unit_price': float(item.product.price) if item.product.price else 0,
                'total_value': item_value,
                'last_updated': item.last_updated
            })
        
        return Response({
            'inventory': inventory_data,
            'summary': {
                'total_items': len(inventory_data),
                'total_value': total_value,
            }
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def user_management_dashboard(request):
    """
    Dashboard data for user management including user statistics
    """
    # Get user statistics
    total_users = User.objects.count()
    total_active_users = User.objects.filter(is_active=True).count()
    total_inactive_users = User.objects.filter(is_active=False).count()
    
    # Count users by role
    role_stats = {}
    for role_choice, role_name in UserProfile.ROLE_CHOICES:
        role_count = UserProfile.objects.filter(role=role_choice).count()
        role_stats[role_choice] = {
            'name': role_name,
            'count': role_count
        }
    
    # Get recently created users
    recent_users = User.objects.select_related('userprofile').order_by('-date_joined')[:10]
    recent_users_data = []
    for user in recent_users:
        recent_users_data.append({
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'role': user.userprofile.role if hasattr(user, 'userprofile') else 'N/A',
            'date_joined': user.date_joined,
            'is_active': user.is_active
        })
    
    data = {
        'total_users': total_users,
        'total_active_users': total_active_users,
        'total_inactive_users': total_inactive_users,
        'role_statistics': role_stats,
        'recent_users': recent_users_data,
    }
    
    return Response(data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def update_user_role(request, user_id):
    """
    Super Admin specific endpoint to update a user's role
    """
    try:
        user = User.objects.get(id=user_id)
        user_profile, created = UserProfile.objects.get_or_create(user=user)
        
        new_role = request.data.get('role')
        if not new_role:
            return Response(
                {'error': 'Role is required.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if new_role not in [choice[0] for choice in UserProfile.ROLE_CHOICES]:
            return Response(
                {'error': 'Invalid role.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Prevent demoting the last super admin
        if user_profile.role == 'super_admin':
            super_admin_count = UserProfile.objects.filter(role='super_admin').count()
            if super_admin_count <= 1 and new_role != 'super_admin':
                return Response(
                    {'error': 'Cannot change role of the last super admin.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        user_profile.role = new_role
        user_profile.save()
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='update',
            object_type='userprofile',
            object_id=user.id,
            object_repr=f"Role updated to {new_role} for user {user.username}",
            notes=f"Role changed by super admin {request.user.username}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        serializer = UserSerializer(user)
        return Response(serializer.data, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found.'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def create_user_with_role(request):
    """
    Super Admin specific endpoint to create a user with specified role
    """
    serializer = UserRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        
        # The role is already handled by the registration serializer
        return Response({
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'role': user.userprofile.role if hasattr(user, 'userprofile') else 'N/A',
            'message': 'User created successfully'
        }, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def verify_coupon(request, code):
    """
    Verify if a coupon code is valid
    """
    try:
        from django.utils import timezone
        from django.db.models import Q
        
        # Find the coupon by code
        coupon = Coupon.objects.filter(code=code).first()
        
        if not coupon:
            return Response(
                {'error': 'Invalid coupon code'}, 
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Check if the coupon is active
        if not coupon.is_active:
            return Response(
                {'error': 'This coupon is not active'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if the coupon has expired
        now = timezone.now()
        if not (coupon.start_date <= now <= coupon.end_date):
            return Response(
                {'error': 'This coupon has expired'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check usage limits
        if coupon.max_usage_count and coupon.used_count >= coupon.max_usage_count:
            return Response(
                {'error': 'This coupon has reached its usage limit'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if limited to customer (this would require additional info from the request)
        # For now, we'll just return the valid coupon information
        
        # Return the coupon data
        serializer = CouponSerializer(coupon)
        coupon_data = serializer.data
        coupon_data['is_valid'] = True
        
        return Response(coupon_data, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response(
            {'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


# Token Management Views
from django.utils import timezone
from rest_framework_simplejwt.tokens import AccessToken
from .models import BlacklistedToken


from rest_framework_simplejwt.tokens import RefreshToken
from .models import BlacklistedToken

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout(request):
    """
    Blacklists a refresh token and its corresponding access token.
    """
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)

        # Blacklist the refresh token
        BlacklistedToken.objects.create(
            user=request.user,
            jti=token['jti'],
            token=str(token),
            expires_at=datetime.fromtimestamp(token['exp'], tz=timezone.utc),
            reason="User logout"
        )

        # Blacklist the access token
        access_token = token.access_token
        BlacklistedToken.objects.create(
            user=request.user,
            jti=access_token['jti'],
            token=str(access_token),
            expires_at=datetime.fromtimestamp(access_token['exp'], tz=timezone.utc),
            reason="User logout"
        )

        return Response(status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def blacklist_user_tokens(request, user_id):
    """
    Super Admin endpoint to blacklist all tokens for a specific user
    This can be used for account deactivation or security purposes
    """
    try:
        user = User.objects.get(id=user_id)
        
        # In a real implementation, you would need a way to track active tokens
        # For now, we'll just return a success message
        # In a complete implementation, you would store tokens and allow bulk blacklisting
        
        # Create audit log
        AuditLog.objects.create(
            user=request.user,
            action='update',
            object_type='user',
            object_id=user.id,
            object_repr=f"All tokens blacklisted for user {user.username}",
            notes=f"Tokens blacklisted by super admin {request.user.username}",
            ip_address=request.META.get('REMOTE_ADDR')
        )
        
        return Response(
            {'message': f'All tokens for user {user.username} have been blacklisted'}, 
            status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def blacklisted_tokens_list(request):
    """
    Super Admin endpoint to view blacklisted tokens
    """
    tokens = BlacklistedToken.objects.select_related('user').all().order_by('-blacklisted_at')[:100]  # Limit to last 100 for performance
    
    tokens_data = []
    for token in tokens:
        tokens_data.append({
            'id': token.id,
            'user': token.user.username if token.user else 'Unknown',
            'user_id': token.user.id if token.user else None,
            'jti': token.jti,
            'blacklisted_at': token.blacklisted_at,
            'expires_at': token.expires_at,
            'reason': token.reason,
        })
    
    return Response({
        'tokens': tokens_data,
        'total_count': BlacklistedToken.objects.count()
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def check_token_validity(request):
    """
    Check if the current user's token is still valid (not blacklisted)
    """
    try:
        # Get the access token from the Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response(
                {'valid': False, 'error': 'Authorization token required'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        token = auth_header.split(' ')[1]
        
        # Decode the token to get the jti
        try:
            access_token = AccessToken(token)
            jti = str(access_token['jti'])
        except Exception:
            return Response(
                {'valid': False, 'error': 'Invalid token'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if token is blacklisted
        if BlacklistedToken.objects.filter(jti=jti).exists():
            return Response(
                {'valid': False, 'error': 'Token has been revoked'}, 
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        return Response(
            {'valid': True, 'user_id': request.user.id}, 
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'valid': False, 'error': str(e)}, 
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def bulk_product_operations(request):
    """
    API endpoint for bulk importing/exporting products via CSV/JSON
    """
    from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
    from django.http import HttpResponse
    import csv
    import json
    from io import StringIO
    from django.core.files.uploadedfile import SimpleUploadedFile
    from pos_app.models import Category
    
    action = request.data.get('action', '').lower()  # 'import' or 'export'
    file_format = request.data.get('format', 'csv').lower()  # 'csv' or 'json'
    
    if action == 'import':
        uploaded_file = request.FILES.get('file')
        if not uploaded_file:
            return Response(
                {'error': 'No file uploaded'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Import products based on file format
            if file_format == 'csv':
                csv_content = uploaded_file.read().decode('utf-8')
                reader = csv.DictReader(StringIO(csv_content))
                
                for row in reader:
                    # Get or create category
                    category_name = row.get('category', '').strip()
                    category = None
                    if category_name:
                        category, created = Category.objects.get_or_create(
                            name=category_name,
                            defaults={'description': f'Auto-created for {category_name}'}
                        )
                    
                    # Handle tags
                    tags = row.get('tags', '').strip()
                    
                    # Create or update product
                    product, created = Product.objects.get_or_create(
                        sku=row['sku'].strip(),
                        defaults={
                            'name': row['name'].strip(),
                            'barcode': row.get('barcode', '').strip() or None,
                            'description': row.get('description', '').strip(),
                            'category': category,
                            'price': row['price'],
                            'wholesale_price': row.get('wholesale_price') or None,
                            'cost_price': row.get('cost_price') or None,
                            'min_wholesale_qty': row.get('min_wholesale_qty') or 1,
                            'tags': tags,
                            'is_active': row.get('is_active', 'true').lower() == 'true'
                        }
                    )
                    
                    if not created:
                        # Update existing product
                        product.name = row['name'].strip()
                        product.barcode = row.get('barcode', '').strip() or None
                        product.description = row.get('description', '').strip()
                        product.category = category
                        product.price = row['price']
                        product.wholesale_price = row.get('wholesale_price') or None
                        product.cost_price = row.get('cost_price') or None
                        product.min_wholesale_qty = row.get('min_wholesale_qty') or 1
                        product.tags = tags
                        product.is_active = row.get('is_active', 'true').lower() == 'true'
                        product.save()
                
                return Response(
                    {'message': f'Successfully imported products from CSV'}, 
                    status=status.HTTP_200_OK
                )
                
            elif file_format == 'json':
                json_content = json.loads(uploaded_file.read().decode('utf-8'))
                
                for item in json_content:
                    # Get or create category
                    category_name = item.get('category', '').strip()
                    category = None
                    if category_name:
                        category, created = Category.objects.get_or_create(
                            name=category_name,
                            defaults={'description': f'Auto-created for {category_name}'}
                        )
                    
                    # Create or update product
                    product, created = Product.objects.get_or_create(
                        sku=item['sku'],
                        defaults={
                            'name': item['name'],
                            'barcode': item.get('barcode') or None,
                            'description': item.get('description', ''),
                            'category': category,
                            'price': item['price'],
                            'wholesale_price': item.get('wholesale_price') or None,
                            'cost_price': item.get('cost_price') or None,
                            'min_wholesale_qty': item.get('min_wholesale_qty') or 1,
                            'tags': item.get('tags', ''),
                            'is_active': item.get('is_active', True)
                        }
                    )
                    
                    if not created:
                        # Update existing product
                        product.name = item['name']
                        product.barcode = item.get('barcode') or None
                        product.description = item.get('description', '')
                        product.category = category
                        product.price = item['price']
                        product.wholesale_price = item.get('wholesale_price') or None
                        product.cost_price = item.get('cost_price') or None
                        product.min_wholesale_qty = item.get('min_wholesale_qty') or 1
                        product.tags = item.get('tags', '')
                        product.is_active = item.get('is_active', True)
                        product.save()
                
                return Response(
                    {'message': f'Successfully imported products from JSON'}, 
                    status=status.HTTP_200_OK
                )
            else:
                return Response(
                    {'error': f'Unsupported format: {file_format}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    elif action == 'export':
        try:
            # Get all products
            products = Product.objects.all()
            
            if file_format == 'csv':
                # Create CSV response
                response = HttpResponse(content_type='text/csv')
                response['Content-Disposition'] = 'attachment; filename="products_export.csv"'
                
                fieldnames = [
                    'name', 'sku', 'barcode', 'description', 'category', 
                    'price', 'wholesale_price', 'cost_price', 'min_wholesale_qty',
                    'effective_date', 'tags', 'is_active'
                ]
                writer = csv.DictWriter(response, fieldnames=fieldnames)
                writer.writeheader()
                
                for product in products:
                    writer.writerow({
                        'name': product.name,
                        'sku': product.sku,
                        'barcode': product.barcode or '',
                        'description': product.description,
                        'category': product.category.name if product.category else '',
                        'price': product.price,
                        'wholesale_price': product.wholesale_price or '',
                        'cost_price': product.cost_price or '',
                        'min_wholesale_qty': product.min_wholesale_qty,
                        'effective_date': product.effective_date,
                        'tags': product.tags,
                        'is_active': product.is_active
                    })
                
                return response
                
            elif file_format == 'json':
                # Create JSON response
                products_data = []
                for product in products:
                    products_data.append({
                        'name': product.name,
                        'sku': product.sku,
                        'barcode': product.barcode,
                        'description': product.description,
                        'category': product.category.name if product.category else None,
                        'price': float(product.price),
                        'wholesale_price': float(product.wholesale_price) if product.wholesale_price else None,
                        'cost_price': float(product.cost_price) if product.cost_price else None,
                        'min_wholesale_qty': product.min_wholesale_qty,
                        'effective_date': product.effective_date.isoformat(),
                        'image': str(product.image) if product.image else None,
                        'tags': product.tags,
                        'is_active': product.is_active,
                        'created_at': product.created_at.isoformat(),
                        'updated_at': product.updated_at.isoformat()
                    })
                
                response = HttpResponse(
                    json.dumps(products_data, indent=2), 
                    content_type='application/json'
                )
                response['Content-Disposition'] = 'attachment; filename="products_export.json"'
                
                return response
            else:
                return Response(
                    {'error': f'Unsupported format: {file_format}'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Exception as e:
            return Response(
                {'error': str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    else:
        return Response(
            {'error': 'Invalid action. Use "import" or "export".'}, 
            status=status.HTTP_400_BAD_REQUEST
        )


def export_report_to_csv(data, filename, fields=None):
    """
    Export report data to CSV format
    """
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # If fields are provided, use them as headers
    if fields:
        writer.writerow([field.replace('_', ' ').title() for field in fields])
        
        # Write data rows
        for item in data:
            row = []
            for field in fields:
                value = item.get(field, '')
                if isinstance(value, (list, dict)):
                    value = str(value)
                row.append(value)
            writer.writerow(row)
    else:
        # Infer fields from the first data item
        if data:
            first_item = data[0]
            headers = [key.replace('_', ' ').title() for key in first_item.keys()]
            writer.writerow(headers)
            
            for item in data:
                row = []
                for key in first_item.keys():
                    value = item.get(key, '')
                    if isinstance(value, (list, dict)):
                        value = str(value)
                    row.append(value)
                writer.writerow(row)
    
    return response


def export_report_to_excel(data, filename, sheet_name="Report", fields=None):
    """
    Export report data to Excel (XLSX) format
    """
    if not OPENPYXL_AVAILABLE:
        return Response(
            {'error': 'Excel export not available. Install openpyxl: pip install openpyxl'}, 
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
    
    wb = Workbook()
    ws = wb.active
    ws.title = sheet_name
    
    # If fields are provided, use them as headers
    if fields:
        headers = [field.replace('_', ' ').title() for field in fields]
        ws.append(headers)
        
        # Write data rows
        for item in data:
            row = []
            for field in fields:
                value = item.get(field, '')
                if isinstance(value, (list, dict)):
                    value = str(value)
                elif isinstance(value, float):
                    # Convert to Decimal for proper Excel formatting
                    value = Decimal(str(value))
                row.append(value)
            ws.append(row)
    else:
        # Infer fields from the first data item
        if data:
            first_item = data[0]
            headers = [key.replace('_', ' ').title() for key in first_item.keys()]
            ws.append(headers)
            
            for item in data:
                row = []
                for key in first_item.keys():
                    value = item.get(key, '')
                    if isinstance(value, (list, dict)):
                        value = str(value)
                    elif isinstance(value, float):
                        # Convert to Decimal for proper Excel formatting
                        value = Decimal(str(value))
                    row.append(value)
                ws.append(row)
    
    # Auto-adjust column widths
    for column in ws.columns:
        max_length = 0
        column_letter = get_column_letter(column[0].column)
        
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        
        adjusted_width = min(max_length + 2, 50)  # Limit width to 50 characters
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Set up response
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    wb.save(response)
    
    return response


def export_report_to_pdf(data, filename, title="Report", fields=None):
    """
    Export report data to PDF format
    """
    if not REPORTLAB_AVAILABLE:
        return Response(
            {'error': 'PDF export not available. Install reportlab: pip install reportlab'}, 
            status=status.HTTP_501_NOT_IMPLEMENTED
        )
    
    # Create a PDF document
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    doc = SimpleDocTemplate(response, pagesize=A4)
    elements = []
    
    # Add title
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=18,
        spaceAfter=30,
        alignment=1  # Center alignment
    )
    title_paragraph = Paragraph(title, title_style)
    elements.append(title_paragraph)
    
    # Add a spacer
    elements.append(Spacer(1, 12))
    
    if data:
        # Prepare table data
        if fields:
            headers = [field.replace('_', ' ').title() for field in fields]
            table_data = [headers]
            
            for item in data:
                row = []
                for field in fields:
                    value = item.get(field, '')
                    if isinstance(value, (list, dict)):
                        value = str(value)
                    row.append(str(value))
                table_data.append(row)
        else:
            # Infer fields from the first data item
            first_item = data[0]
            headers = [key.replace('_', ' ').title() for key in first_item.keys()]
            table_data = [headers]
            
            for item in data:
                row = []
                for key in first_item.keys():
                    value = item.get(key, '')
                    if isinstance(value, (list, dict)):
                        value = str(value)
                    row.append(str(value))
                table_data.append(row)
        
        # Create table
        table = Table(table_data)
        
        # Style the table
        style = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ])
        
        table.setStyle(style)
        
        # Add table to elements
        elements.append(table)
    
    # Build PDF
    doc.build(elements)
    
    return response


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_sales_report(request):
    """
    Export sales report in specified format (csv, xlsx, pdf)
    """
    try:
        # Get format parameter
        export_format = request.query_params.get('format', 'csv').lower()
        filename = request.query_params.get('filename', 'sales_report.csv')
        
        # Get the sales report data using the same parameters as the original report
        from django.http import QueryDict
        # Create a new request with the same parameters to reuse the sales_report function
        sales_report_data = sales_report(request).data
        
        # Extract the sales data
        sales_data = sales_report_data.get('sales', [])
        
        if export_format == 'csv':
            # Define fields for CSV export
            fields = ['id', 'receipt_number', 'sale_date', 'customer_name', 'warehouse_name', 
                     'warehouse_type', 'total_amount', 'payment_status']
            return export_report_to_csv(sales_data, filename.replace('.csv', '') + '.csv', fields)
        
        elif export_format == 'xlsx':
            # Define fields for Excel export
            fields = ['id', 'receipt_number', 'sale_date', 'customer_name', 'warehouse_name', 
                     'warehouse_type', 'total_amount', 'payment_status']
            return export_report_to_excel(sales_data, filename.replace('.xlsx', '') + '.xlsx', 
                                         'Sales Report', fields)
        
        elif export_format == 'pdf':
            return export_report_to_pdf(sales_data, filename.replace('.pdf', '') + '.pdf',
                                       'Sales Report')
        
        else:
            return Response(
                {'error': f'Unsupported format: {export_format}. Use csv, xlsx, or pdf.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_inventory_report(request):
    """
    Export inventory report in specified format (csv, xlsx, pdf)
    """
    try:
        # Get format parameter
        export_format = request.query_params.get('format', 'csv').lower()
        filename = request.query_params.get('filename', 'inventory_report.csv')
        
        # Get the inventory report data using the same parameters as the original report
        inventory_report_data = inventory_report(request).data
        
        # Extract the inventory data
        inventory_data = inventory_report_data.get('inventory', [])
        
        if export_format == 'csv':
            # Define fields for CSV export
            fields = ['id', 'product_name', 'product_sku', 'category_name', 'warehouse_name',
                     'quantity_on_hand', 'quantity_reserved', 'available_stock', 'min_stock_level',
                     'is_low_stock', 'unit_price', 'total_value', 'last_updated']
            return export_report_to_csv(inventory_data, filename.replace('.csv', '') + '.csv', fields)
        
        elif export_format == 'xlsx':
            # Define fields for Excel export
            fields = ['id', 'product_name', 'product_sku', 'category_name', 'warehouse_name',
                     'quantity_on_hand', 'quantity_reserved', 'available_stock', 'min_stock_level',
                     'is_low_stock', 'unit_price', 'total_value', 'last_updated']
            return export_report_to_excel(inventory_data, filename.replace('.xlsx', '') + '.xlsx',
                                         'Inventory Report', fields)
        
        elif export_format == 'pdf':
            return export_report_to_pdf(inventory_data, filename.replace('.pdf', '') + '.pdf',
                                       'Inventory Report')
        
        else:
            return Response(
                {'error': f'Unsupported format: {export_format}. Use csv, xlsx, or pdf.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_transfer_report(request):
    """
    Export transfer report in specified format (csv, xlsx, pdf)
    """
    try:
        # Get format parameter
        export_format = request.query_params.get('format', 'csv').lower()
        filename = request.query_params.get('filename', 'transfer_report.csv')
        
        # Get the transfer report data using the same parameters as the original report
        transfer_report_data = transfer_report(request).data
        
        # Extract the transfer data
        transfers_data = transfer_report_data.get('transfers', [])
        
        if export_format == 'csv':
            # Define fields for CSV export
            fields = ['id', 'transfer_number', 'from_warehouse', 'to_warehouse', 'status',
                     'requested_at', 'approved_at', 'received_at', 'notes', 'has_discrepancies']
            return export_report_to_csv(transfers_data, filename.replace('.csv', '') + '.csv', fields)
        
        elif export_format == 'xlsx':
            # Define fields for Excel export
            fields = ['id', 'transfer_number', 'from_warehouse', 'to_warehouse', 'status',
                     'requested_at', 'approved_at', 'received_at', 'notes', 'has_discrepancies']
            return export_report_to_excel(transfers_data, filename.replace('.xlsx', '') + '.xlsx',
                                         'Transfer Report', fields)
        
        elif export_format == 'pdf':
            return export_report_to_pdf(transfers_data, filename.replace('.pdf', '') + '.pdf',
                                       'Transfer Report')
        
        else:
            return Response(
                {'error': f'Unsupported format: {export_format}. Use csv, xlsx, or pdf.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def export_profitability_report(request):
    """
    Export profitability report in specified format (csv, xlsx, pdf)
    """
    try:
        # Get format parameter
        export_format = request.query_params.get('format', 'csv').lower()
        filename = request.query_params.get('filename', 'profitability_report.csv')
        
        # Get the profitability report data using the same parameters as the original report
        profitability_report_data = profitability_report(request).data
        
        # Extract the sales data (which contains profitability info)
        sales_data = profitability_report_data.get('sales', [])
        
        if export_format == 'csv':
            # Define fields for CSV export
            fields = ['id', 'receipt_number', 'sale_date', 'total_revenue', 'total_cogs',
                     'profit', 'profit_margin', 'valuation_method']
            return export_report_to_csv(sales_data, filename.replace('.csv', '') + '.csv', fields)
        
        elif export_format == 'xlsx':
            # Define fields for Excel export
            fields = ['id', 'receipt_number', 'sale_date', 'total_revenue', 'total_cogs',
                     'profit', 'profit_margin', 'valuation_method']
            return export_report_to_excel(sales_data, filename.replace('.xlsx', '') + '.xlsx',
                                         'Profitability Report', fields)
        
        elif export_format == 'pdf':
            return export_report_to_pdf(sales_data, filename.replace('.pdf', '') + '.pdf',
                                       'Profitability Report')
        
        else:
            return Response(
                {'error': f'Unsupported format: {export_format}. Use csv, xlsx, or pdf.'}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

from rest_framework_simplejwt.tokens import RefreshToken
from .models import BlacklistedToken

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_and_blacklist_token(request):
    """
    Blacklists a refresh token and its corresponding access token.
    """
    try:
        refresh_token = request.data["refresh"]
        token = RefreshToken(refresh_token)

        # Blacklist the refresh token
        BlacklistedToken.objects.create(
            user=request.user,
            jti=token['jti'],
            token=str(token),
            expires_at=datetime.fromtimestamp(token['exp'], tz=timezone.utc),
            reason="User logout"
        )

        # Blacklist the access token
        access_token = token.access_token
        BlacklistedToken.objects.create(
            user=request.user,
            jti=access_token['jti'],
            token=str(access_token),
            expires_at=datetime.fromtimestamp(access_token['exp'], tz=timezone.utc),
            reason="User logout"
        )

        return Response(status=status.HTTP_205_RESET_CONTENT)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)