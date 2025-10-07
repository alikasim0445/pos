from rest_framework import viewsets, generics, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth import authenticate
from django.contrib.auth.hashers import make_password
from django.db import transaction
from django.db.models import F
from django.http import HttpResponse
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
from .models import (
    User, Category, Product, ProductVariant, Warehouse, 
    Inventory, Customer, Sale, SaleLine, Payment, 
    Transfer, TransferLine, AuditLog, Return, ReturnLine, Promotion, Coupon,
    PurchaseOrder, PurchaseOrderLine, GoodsReceivedNote, GoodsReceivedNoteLine, UserProfile
)
from .serializers import (
    UserSerializer, UserRegistrationSerializer, CategorySerializer, ProductSerializer, ProductVariantSerializer,
    WarehouseSerializer, InventorySerializer, CustomerSerializer,
    SaleSerializer, SaleLineSerializer, PaymentSerializer,
    TransferSerializer, TransferLineSerializer, AuditLogSerializer, ReturnSerializer, ReturnLineSerializer,
    PromotionSerializer, CouponSerializer, PurchaseOrderSerializer, PurchaseOrderLineSerializer,
    GoodsReceivedNoteSerializer, GoodsReceivedNoteLineSerializer
)


# Authentication
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

User = get_user_model()

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
            # Generate tokens
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user_id': user.id,
                'username': user.username,
                'email': user.email,
            })
        
        # If authentication fails
        return Response(
            {'error': 'Invalid credentials'}, 
            status=status.HTTP_401_UNAUTHORIZED
        )


from rest_framework.permissions import AllowAny

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


class ProductDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


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


class SaleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_sale(request):
    """
    Create a new sale with multiple items and payment processing.
    Expected JSON format:
    {
        "cashier_id": 1,
        "customer_id": 1,
        "warehouse_id": 1,
        "items": [
            {"product_id": 1, "variant_id": null, "quantity": 2, "unit_price": 10.99},
            {"product_id": 2, "variant_id": null, "quantity": 1, "unit_price": 5.99}
        ],
        "payments": [
            {"method": "cash", "amount": 27.97}
        ]
    }
    """
    try:
        with transaction.atomic():
            # Extract data from request
            cashier_id = request.data.get('cashier_id')
            customer_id = request.data.get('customer_id')
            warehouse_id = request.data.get('warehouse_id')
            items_data = request.data.get('items', [])
            payments_data = request.data.get('payments', [])
            
            # Get related objects
            cashier = User.objects.get(id=cashier_id)
            customer = Customer.objects.get(id=customer_id) if customer_id else None
            warehouse = Warehouse.objects.get(id=warehouse_id)
            
            # Generate receipt number
            import uuid
            receipt_number = f"RCT-{uuid.uuid4().hex[:8].upper()}"
            
            # Create the sale
            total_amount = sum(item['quantity'] * item['unit_price'] for item in items_data)
            sale = Sale.objects.create(
                receipt_number=receipt_number,
                cashier=cashier,
                customer=customer,
                warehouse=warehouse,
                total_amount=total_amount,
                tax_amount=0,  # Simplified - in a real system you'd calculate tax
                payment_status='completed'  # Assuming immediate completion
            )
            
            # Create sale lines
            for item_data in items_data:
                product = Product.objects.get(id=item_data['product_id'])
                variant = ProductVariant.objects.get(id=item_data['variant_id']) if item_data.get('variant_id') else None
                
                SaleLine.objects.create(
                    sale=sale,
                    product=product,
                    variant=variant,
                    quantity=item_data['quantity'],
                    unit_price=item_data['unit_price'],
                    total_price=item_data['quantity'] * item_data['unit_price'],
                    discount_percent=item_data.get('discount_percent', 0)
                )
                
                # Update inventory
                inventory = Inventory.objects.get(
                    product=product,
                    variant=variant,
                    warehouse=warehouse
                )
                inventory.qty_on_hand -= item_data['quantity']
                inventory.save()
            
            # Create payment records
            for payment_data in payments_data:
                Payment.objects.create(
                    sale=sale,
                    payment_method=payment_data['method'],
                    amount=payment_data['amount'],
                    reference=f"PAY-{uuid.uuid4().hex[:8].upper()}"
                )
            
            # Serialize and return the created sale
            serializer = SaleSerializer(sale)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_receipt(request, sale_id):
    """
    Generate and return a receipt for a specific sale in PDF format.
    """
    try:
        # Try to import WeasyPrint - only when needed, not at module level
        try:
            from weasyprint import HTML
        except ImportError:
            return Response({'error': 'PDF generation library not available. Install WeasyPrint with its dependencies.'}, 
                          status=status.HTTP_501_NOT_IMPLEMENTED)
        
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
        
        # Generate PDF
        html = HTML(string=html_string)
        pdf = html.write_pdf()
        
        # Create HTTP response with PDF
        response = HttpResponse(pdf, content_type='application/pdf')
        response['Content-Disposition'] = f'attachment; filename="receipt_{sale.receipt_number}.pdf"'
        return response
        
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

# Return/Exchange Views
class ReturnListView(generics.ListCreateAPIView):
    queryset = Return.objects.all()
    serializer_class = ReturnSerializer
    permission_classes = [IsAuthenticated]

class ReturnDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Return.objects.all()
    serializer_class = ReturnSerializer
    permission_classes = [IsAuthenticated]

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
                'phone': customer.phone
            },
            'purchase_history': history_data,
            'total_orders': len(history_data),
            'total_spent': total_spent
        })
        
    except Customer.DoesNotExist:
        return Response({'error': 'Customer not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def low_stock_alerts(request):
    """
    Get all low stock items
    """
    try:
        # Get all inventory items where available stock is below min_stock_level
        low_stock_items = Inventory.objects.filter(
            qty_on_hand__lt=F('min_stock_level')
        ).select_related('product', 'warehouse')
        
        # Prepare the response data
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
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


# Report Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sales_report(request):
    """
    Generate sales report by period, store, warehouse, or SKU
    """
    try:
        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        warehouse_id = request.query_params.get('warehouse_id')
        sku = request.query_params.get('sku')
        
        # Build query filters
        sales_query = Sale.objects.all()
        
        if start_date:
            sales_query = sales_query.filter(sale_date__gte=start_date)
        if end_date:
            sales_query = sales_query.filter(sale_date__lte=end_date)
        if warehouse_id:
            sales_query = sales_query.filter(warehouse_id=warehouse_id)
        
        # Get sales with related data
        sales = sales_query.prefetch_related('lines__product', 'payments').order_by('-sale_date')
        
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
                'total_amount': sale_total,
                'payment_status': sale.payment_status,
                'items': []
            }
            
            # Add items to sale
            for line in sale.lines.all():
                sale_data['items'].append({
                    'product_name': line.product.name,
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
    """
    Generate inventory report with stock levels and aging
    """
    try:
        # Get query parameters
        warehouse_id = request.query_params.get('warehouse_id')
        category_id = request.query_params.get('category_id')
        
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
            
            report_data.append({
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
            })
        
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
    """
    Generate profitability report (revenue, COGS)
    """
    try:
        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        # Build query filters
        sales_query = Sale.objects.all()
        
        if start_date:
            sales_query = sales_query.filter(sale_date__gte=start_date)
        if end_date:
            sales_query = sales_query.filter(sale_date__lte=end_date)
        
        # Get sales with related data
        sales = sales_query.prefetch_related('lines__product').order_by('-sale_date')
        
        # Prepare report data
        report_data = []
        total_revenue = 0
        total_cogs = 0  # Cost of Goods Sold
        
        for sale in sales:
            sale_revenue = float(sale.total_amount)
            sale_cogs = 0
            profit = 0
            
            # Calculate COGS and profit for this sale
            for line in sale.lines.all():
                cost_price = float(line.cost_price) if line.cost_price else 0
                line_cogs = cost_price * line.quantity
                sale_cogs += line_cogs
            
            profit = sale_revenue - sale_cogs
            total_revenue += sale_revenue
            total_cogs += sale_cogs
            
            report_data.append({
                'id': sale.id,
                'receipt_number': sale.receipt_number,
                'sale_date': sale.sale_date,
                'total_revenue': sale_revenue,
                'total_cogs': sale_cogs,
                'profit': profit,
                'profit_margin': (profit / sale_revenue * 100) if sale_revenue > 0 else 0
            })
        
        overall_profit = total_revenue - total_cogs
        overall_margin = (overall_profit / total_revenue * 100) if total_revenue > 0 else 0
        
        return Response({
            'sales': report_data,
            'summary': {
                'total_revenue': total_revenue,
                'total_cogs': total_cogs,
                'total_profit': overall_profit,
                'overall_profit_margin': overall_margin,
                'date_range': f"{start_date or 'Start'} to {end_date or 'Now'}"
            }
        })
        
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def transfer_report(request):
    """
    Generate transfer history report
    """
    try:
        # Get query parameters
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        from_warehouse_id = request.query_params.get('from_warehouse_id')
        to_warehouse_id = request.query_params.get('to_warehouse_id')
        
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
                'items': []
            }
            
            # Add items to transfer
            for line in transfer.lines.all():
                transfer_data['items'].append({
                    'product_name': line.product.name,
                    'requested_qty': line.requested_qty,
                    'transferred_qty': line.transferred_qty,
                    'received_qty': line.received_qty,
                })
            
            report_data.append(transfer_data)
        
        return Response({
            'transfers': report_data,
            'summary': {
                'total_transfers': len(report_data),
                'date_range': f"{start_date or 'Start'} to {end_date or 'Now'}"
            }
        })
        
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
        
        return Response({'message': 'Password successfully reset'}, status=status.HTTP_200_OK)
    else:
        return Response({'error': 'Invalid reset link'}, status=status.HTTP_400_BAD_REQUEST)


# ViewSets
class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [IsAuthenticated]


class WarehouseViewSet(viewsets.ModelViewSet):
    queryset = Warehouse.objects.all()
    serializer_class = WarehouseSerializer
    permission_classes = [IsAuthenticated]


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all()
    serializer_class = SaleSerializer
    permission_classes = [IsAuthenticated]


# Super Admin specific user management views
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
        
        return super().destroy(request, *args, **kwargs)


@api_view(['POST'])
@permission_classes([IsAuthenticated, IsSuperAdmin])
def reset_user_password(request, user_id):
    """
    Super Admin specific endpoint to reset any user's password
    """
    try:
        user = User.objects.get(id=user_id)
        
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