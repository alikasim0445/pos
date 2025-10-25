import requests
import json
import hashlib
import hmac
from datetime import datetime
from django.utils import timezone
from .models import Webhook, WebhookLog


class WebhookService:
    """
    Service class to handle webhook operations
    """
    
    @staticmethod
    def trigger_webhook(event_type, payload_data):
        """
        Trigger webhooks for a specific event type with the provided payload
        """
        # Get all active webhooks for this event type
        webhooks = Webhook.objects.filter(event_type=event_type, is_active=True)
        
        if not webhooks.exists():
            return  # No webhooks configured for this event
        
        for webhook in webhooks:
            WebhookService._send_webhook(webhook, payload_data)
    
    @staticmethod
    def _send_webhook(webhook, payload_data):
        """
        Send a single webhook with error handling and logging
        """
        try:
            # Prepare the payload
            payload = {
                'event_type': webhook.event_type,
                'timestamp': timezone.now().isoformat(),
                'data': payload_data
            }
            
            # Create signature if secret is provided
            headers = webhook.headers.copy()
            if webhook.secret:
                signature = WebhookService._create_signature(webhook.secret, json.dumps(payload, sort_keys=True))
                headers['X-Signature'] = signature
            
            # Send the webhook request
            response = requests.post(
                webhook.target_url,
                json=payload,
                headers=headers,
                timeout=30  # 30 second timeout
            )
            
            # Log the result
            WebhookLog.objects.create(
                webhook=webhook,
                payload=payload,
                response_status=response.status_code,
                response_content=response.text[:500],  # Limit to 500 chars to prevent large logs
                success=response.ok,
                error_message='' if response.ok else f"HTTP {response.status_code}: {response.text[:200]}"
            )
            
            # Update last triggered timestamp
            webhook.last_triggered = timezone.now()
            webhook.save(update_fields=['last_triggered'])
            
        except requests.exceptions.RequestException as e:
            # Log the error
            WebhookLog.objects.create(
                webhook=webhook,
                payload=payload,
                success=False,
                error_message=str(e)
            )
        except Exception as e:
            # Log any other errors
            WebhookLog.objects.create(
                webhook=webhook,
                payload=payload,
                success=False,
                error_message=f"Unexpected error: {str(e)}"
            )
    
    @staticmethod
    def _create_signature(secret, payload):
        """
        Create HMAC signature for webhook payload
        """
        return hmac.new(
            secret.encode('utf-8'),
            payload.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()


def trigger_sale_completed_webhooks(sale):
    """
    Trigger webhooks for sale completed event
    """
    from .serializers import SaleSerializer
    
    # Serialize the sale data
    serializer = SaleSerializer(sale)
    sale_data = serializer.data
    
    # Trigger the webhook
    WebhookService.trigger_webhook('sale_completed', {
        'sale': sale_data,
        'receipt_number': sale.receipt_number,
        'customer_id': sale.customer.id if sale.customer else None,
        'total_amount': float(sale.total_amount),
        'items_count': sale.lines.count()
    })


def trigger_stock_level_changed_webhooks(inventory_item, old_quantity, new_quantity):
    """
    Trigger webhooks for stock level changed event
    """
    from .serializers import InventorySerializer
    
    # Serialize the inventory data
    serializer = InventorySerializer(inventory_item)
    inventory_data = serializer.data
    
    # Trigger the webhook
    WebhookService.trigger_webhook('stock_level_changed', {
        'inventory': inventory_data,
        'product_name': inventory_item.product.name,
        'product_sku': inventory_item.product.sku,
        'warehouse': inventory_item.warehouse.name,
        'old_quantity': old_quantity,
        'new_quantity': new_quantity,
        'quantity_change': new_quantity - old_quantity,
        'is_low_stock': inventory_item.is_low_stock()
    })


class PaymentGatewayService:
    """
    Service class to handle payment gateway operations
    """
    
    @staticmethod
    def get_gateway_config(gateway_name):
        """
        Get the configuration for a specific payment gateway
        """
        from .models import PaymentGatewayConfig
        try:
            return PaymentGatewayConfig.objects.get(gateway=gateway_name, is_active=True)
        except PaymentGatewayConfig.DoesNotExist:
            return None
    
    @staticmethod
    def process_payment(sale, amount, payment_method_data, customer=None):
        """
        Process a payment using the configured payment gateway
        """
        import stripe
        import paypalrestsdk
        
        # Determine which gateway to use based on payment method data
        gateway = payment_method_data.get('gateway', 'stripe')
        config = PaymentGatewayService.get_gateway_config(gateway)
        
        if not config:
            raise Exception(f"Payment gateway {gateway} is not configured")
        
        if gateway == 'stripe':
            return PaymentGatewayService._process_stripe_payment(
                sale, amount, payment_method_data, customer, config
            )
        elif gateway == 'paypal':
            return PaymentGatewayService._process_paypal_payment(
                sale, amount, payment_method_data, customer, config
            )
        else:
            raise Exception(f"Payment gateway {gateway} not supported")
    
    @staticmethod
    def _process_stripe_payment(sale, amount, payment_method_data, customer, config):
        """
        Process payment using Stripe
        """
        import stripe
        
        # Initialize Stripe with the secret key
        stripe.api_key = config.secret_key
        
        try:
            # Create a payment intent
            intent = stripe.PaymentIntent.create(
                amount=int(amount * 100),  # Amount in cents
                currency='usd',
                payment_method=payment_method_data.get('payment_method_id'),
                customer=customer.stripe_customer_id if customer and hasattr(customer, 'stripe_customer_id') else None,
                confirm=True,
                return_url=f"http://localhost:3000/sale/{sale.id}/payment-success",
                metadata={
                    'sale_id': str(sale.id),
                    'customer_id': str(customer.id) if customer else 'anonymous'
                }
            )
            
            # Check if payment was successful
            if intent.status == 'succeeded':
                return {
                    'success': True,
                    'transaction_id': intent.id,
                    'amount': amount,
                    'gateway': 'stripe',
                    'status': 'succeeded',
                    'payment_method_data': {
                        'brand': intent.payment_method_details.get('card', {}).get('brand', 'unknown'),
                        'last4': intent.payment_method_details.get('card', {}).get('last4', '****')
                    }
                }
            else:
                return {
                    'success': False,
                    'error': f"Payment failed with status: {intent.status}",
                    'gateway': 'stripe'
                }
                
        except stripe.error.CardError as e:
            return {
                'success': False,
                'error': f"Card error: {str(e.user_message)}",
                'gateway': 'stripe'
            }
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'gateway': 'stripe'
            }
    
    @staticmethod
    def _process_paypal_payment(sale, amount, payment_method_data, customer, config):
        """
        Process payment using PayPal
        """
        import paypalrestsdk
        
        # Configure PayPal SDK
        paypalrestsdk.configure({
            "mode": "sandbox" if config.is_sandbox else "live",
            "client_id": config.public_key,
            "client_secret": config.secret_key
        })
        
        try:
            # Create payment
            payment = paypalrestsdk.Payment({
                "intent": "sale",
                "payer": {
                    "payment_method": "credit_card",
                    "funding_instruments": [{
                        "credit_card": {
                            "type": payment_method_data.get('card_type', 'visa'),
                            "number": payment_method_data.get('card_number'),
                            "expire_month": payment_method_data.get('expiry_month'),
                            "expire_year": payment_method_data.get('expiry_year'),
                            "cvv2": payment_method_data.get('cvv'),
                            "first_name": customer.first_name if customer else "Customer",
                            "last_name": customer.last_name if customer else "Unknown"
                        }
                    }]
                },
                "transactions": [{
                    "amount": {
                        "total": f"{amount:.2f}",
                        "currency": "USD"
                    },
                    "description": f"Payment for sale {sale.receipt_number}"
                }]
            })
            
            # Create the payment
            if payment.create():
                # Execute the payment if approved
                if payment.state == "approved":
                    for transaction in payment.transactions:
                        related_resource = transaction.related_resources[0]
                        sale_id = related_resource.sale.id
                        
                        return {
                            'success': True,
                            'transaction_id': sale_id,
                            'amount': amount,
                            'gateway': 'paypal',
                            'status': 'completed',
                            'payment_method_data': {
                                'type': 'credit_card'
                            }
                        }
                else:
                    return {
                        'success': False,
                        'error': f"Payment not approved: {payment.state}",
                        'gateway': 'paypal'
                    }
            else:
                return {
                    'success': False,
                    'error': payment.error,
                    'gateway': 'paypal'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'gateway': 'paypal'
            }
    
    @staticmethod
    def create_customer_token(customer, payment_method_data, gateway_name='stripe'):
        """
        Create a customer token in the payment gateway
        """
        import stripe
        
        config = PaymentGatewayService.get_gateway_config(gateway_name)
        if not config:
            raise Exception(f"Payment gateway {gateway_name} is not configured")
        
        if gateway_name == 'stripe':
            stripe.api_key = config.secret_key
            
            try:
                # Create or retrieve customer in Stripe
                stripe_customer = stripe.Customer.create(
                    email=customer.email,
                    name=f"{customer.first_name} {customer.last_name}",
                    source=payment_method_data.get('source')  # obtained with Stripe.js
                )
                
                # Create a payment method token
                payment_method = stripe.PaymentMethod.create(
                    type="card",
                    card={
                        "number": payment_method_data.get('number'),
                        "exp_month": payment_method_data.get('exp_month'),
                        "exp_year": payment_method_data.get('exp_year'),
                        "cvc": payment_method_data.get('cvc')
                    }
                )
                
                # Attach payment method to customer
                stripe.PaymentMethod.attach(
                    payment_method.id,
                    customer=stripe_customer.id
                )
                
                # Store the token in our database
                from .models import PaymentToken
                token = PaymentToken.objects.create(
                    customer=customer,
                    token=payment_method.id,
                    gateway=gateway_name,
                    masked_card_number=f"****{payment_method_data.get('number')[-4:]}",
                    expiry_month=payment_method_data.get('exp_month'),
                    expiry_year=payment_method_data.get('exp_year'),
                    card_brand=payment_method_data.get('brand', 'Unknown')
                )
                
                return token
            except Exception as e:
                raise e


class EcommerceSyncService:
    """
    Service class to handle e-commerce synchronization
    """
    
    @staticmethod
    def sync_products_to_ecommerce(platform):
        """
        Sync products from POS to e-commerce platform
        """
        from .models import Product, ProductVariant
        
        # Log the sync operation
        sync_log = EcommerceSyncLog.objects.create(
            platform=platform,
            sync_type='product',
            status='started',
            total_records=0
        )
        
        try:
            # Get all active products
            products = Product.objects.filter(is_active=True)
            records_synced = 0
            
            for product in products:
                # Format product data for e-commerce platform
                product_data = EcommerceSyncService._format_product_for_ecommerce(product)
                
                # Send to e-commerce platform based on platform type
                success = EcommerceSyncService._send_product_to_platform(platform, product_data)
                
                if success:
                    records_synced += 1
            
            # Update sync log
            sync_log.status = 'success'
            sync_log.records_synced = records_synced
            sync_log.total_records = products.count()
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            # Update platform last sync time
            platform.last_sync = timezone.now()
            platform.save(update_fields=['last_sync'])
            
            return {
                'success': True,
                'records_synced': records_synced,
                'total_records': products.count()
            }
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def sync_inventory_to_ecommerce(platform):
        """
        Sync inventory levels from POS to e-commerce platform
        """
        from .models import Inventory
        
        # Log the sync operation
        sync_log = EcommerceSyncLog.objects.create(
            platform=platform,
            sync_type='inventory',
            status='started',
            total_records=0
        )
        
        try:
            # Get all inventory items
            inventory_items = Inventory.objects.select_related('product', 'warehouse').all()
            records_synced = 0
            
            for item in inventory_items:
                # Format inventory data for e-commerce platform
                inventory_data = {
                    'sku': item.product.sku,
                    'quantity': item.available_stock(),  # Use available stock (on hand - reserved)
                    'product_name': item.product.name
                }
                
                # Send to e-commerce platform
                success = EcommerceSyncService._send_inventory_to_platform(platform, inventory_data)
                
                if success:
                    records_synced += 1
            
            # Update sync log
            sync_log.status = 'success'
            sync_log.records_synced = records_synced
            sync_log.total_records = inventory_items.count()
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            # Update platform last sync time
            platform.last_sync = timezone.now()
            platform.save(update_fields=['last_sync'])
            
            return {
                'success': True,
                'records_synced': records_synced,
                'total_records': inventory_items.count()
            }
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def sync_orders_from_ecommerce(platform):
        """
        Sync orders from e-commerce platform to POS
        """
        # Log the sync operation
        sync_log = EcommerceSyncLog.objects.create(
            platform=platform,
            sync_type='order',
            status='started',
            total_records=0
        )
        
        try:
            # Fetch orders from e-commerce platform
            ecommerce_orders = EcommerceSyncService._fetch_orders_from_platform(platform)
            records_synced = 0
            
            for order_data in ecommerce_orders:
                # Create or update order in POS system
                success = EcommerceSyncService._create_pos_order_from_ecommerce(platform, order_data)
                
                if success:
                    records_synced += 1
            
            # Update sync log
            sync_log.status = 'success'
            sync_log.records_synced = records_synced
            sync_log.total_records = len(ecommerce_orders)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            # Update platform last sync time
            platform.last_sync = timezone.now()
            platform.save(update_fields=['last_sync'])
            
            return {
                'success': True,
                'records_synced': records_synced,
                'total_records': len(ecommerce_orders)
            }
            
        except Exception as e:
            sync_log.status = 'failed'
            sync_log.error_message = str(e)
            sync_log.completed_at = timezone.now()
            sync_log.save()
            
            return {
                'success': False,
                'error': str(e)
            }
    
    @staticmethod
    def _format_product_for_ecommerce(product):
        """
        Format product data for e-commerce platform
        """
        return {
            'name': product.name,
            'sku': product.sku,
            'description': product.description,
            'price': float(product.price),
            'category': product.category.name if product.category else None,
            'tags': product.tags.split(',') if product.tags else [],
            'is_active': product.is_active
        }
    
    @staticmethod
    def _send_product_to_platform(platform, product_data):
        """
        Send product data to e-commerce platform
        """
        import requests
        import json
        
        try:
            if platform.platform == 'shopify':
                # Shopify API implementation
                headers = {
                    'Content-Type': 'application/json',
                    'X-Shopify-Access-Token': platform.api_secret
                }
                
                payload = {
                    'product': {
                        'title': product_data['name'],
                        'body_html': product_data['description'],
                        'vendor': 'POS System',
                        'product_type': product_data['category'] or 'Default',
                        'status': 'active' if product_data['is_active'] else 'draft',
                        'published': product_data['is_active'],
                        'tags': ','.join(product_data['tags']),
                        'variants': [{
                            'sku': product_data['sku'],
                            'price': product_data['price']
                        }]
                    }
                }
                
                response = requests.post(
                    f"{platform.api_url}/admin/api/2023-01/products.json",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                return response.ok
            
            elif platform.platform == 'woocommerce':
                # WooCommerce API implementation
                import base64
                
                credentials = base64.b64encode(f"{platform.api_key}:{platform.api_secret}".encode()).decode()
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Basic {credentials}'
                }
                
                payload = {
                    'name': product_data['name'],
                    'sku': product_data['sku'],
                    'description': product_data['description'],
                    'regular_price': str(product_data['price']),
                    'manage_stock': True,
                    'status': 'publish' if product_data['is_active'] else 'draft'
                }
                
                response = requests.post(
                    f"{platform.api_url}/wp-json/wc/v3/products",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                return response.ok
            
            elif platform.platform == 'custom':
                # For custom API implementations
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {platform.api_key}'
                }
                
                payload = {
                    'product': product_data
                }
                
                response = requests.post(
                    f"{platform.api_url}/products",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                return response.ok
                
        except Exception:
            return False
    
    @staticmethod
    def _send_inventory_to_platform(platform, inventory_data):
        """
        Send inventory data to e-commerce platform
        """
        import requests
        
        try:
            if platform.platform == 'shopify':
                # First, we need to get the Shopify product ID to update inventory
                headers = {
                    'Content-Type': 'application/json',
                    'X-Shopify-Access-Token': platform.api_secret
                }
                
                # Search for the product by SKU
                search_response = requests.get(
                    f"{platform.api_url}/admin/api/2023-01/products.json?sku={inventory_data['sku']}",
                    headers=headers,
                    timeout=30
                )
                
                if search_response.ok and search_response.json().get('products'):
                    product = search_response.json()['products'][0]
                    
                    # Update the first variant's inventory
                    if product['variants']:
                        variant_id = product['variants'][0]['id']
                        
                        update_data = {
                            'variant': {
                                'id': variant_id,
                                'inventory_quantity': inventory_data['quantity']
                            }
                        }
                        
                        response = requests.put(
                            f"{platform.api_url}/admin/api/2023-01/variants/{variant_id}.json",
                            headers=headers,
                            json=update_data,
                            timeout=30
                        )
                        
                        return response.ok
            
            elif platform.platform == 'woocommerce':
                import base64
                credentials = base64.b64encode(f"{platform.api_key}:{platform.api_secret}".encode()).decode()
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Basic {credentials}'
                }
                
                # Search for the product by SKU
                search_response = requests.get(
                    f"{platform.api_url}/wp-json/wc/v3/products?sku={inventory_data['sku']}",
                    headers=headers,
                    timeout=30
                )
                
                if search_response.ok:
                    products = search_response.json()
                    if products:
                        product_id = products[0]['id']
                        
                        update_data = {
                            'stock_quantity': inventory_data['quantity'],
                            'manage_stock': True
                        }
                        
                        response = requests.put(
                            f"{platform.api_url}/wp-json/wc/v3/products/{product_id}",
                            headers=headers,
                            json=update_data,
                            timeout=30
                        )
                        
                        return response.ok
            
            elif platform.platform == 'custom':
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {platform.api_key}'
                }
                
                payload = {
                    'sku': inventory_data['sku'],
                    'quantity': inventory_data['quantity'],
                    'product_name': inventory_data['product_name']
                }
                
                response = requests.post(
                    f"{platform.api_url}/inventory/update",
                    headers=headers,
                    json=payload,
                    timeout=30
                )
                
                return response.ok
                
            return False
            
        except Exception:
            return False
    
    @staticmethod
    def _fetch_orders_from_platform(platform):
        """
        Fetch orders from e-commerce platform
        """
        import requests
        
        try:
            if platform.platform == 'shopify':
                headers = {
                    'Content-Type': 'application/json',
                    'X-Shopify-Access-Token': platform.api_secret
                }
                
                response = requests.get(
                    f"{platform.api_url}/admin/api/2023-01/orders.json",
                    headers=headers,
                    timeout=30
                )
                
                if response.ok:
                    return response.json().get('orders', [])
            
            elif platform.platform == 'woocommerce':
                import base64
                credentials = base64.b64encode(f"{platform.api_key}:{platform.api_secret}".encode()).decode()
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Basic {credentials}'
                }
                
                response = requests.get(
                    f"{platform.api_url}/wp-json/wc/v3/orders",
                    headers=headers,
                    timeout=30
                )
                
                if response.ok:
                    return response.json()
            
            elif platform.platform == 'custom':
                headers = {
                    'Content-Type': 'application/json',
                    'Authorization': f'Bearer {platform.api_key}'
                }
                
                response = requests.get(
                    f"{platform.api_url}/orders",
                    headers=headers,
                    timeout=30
                )
                
                if response.ok:
                    return response.json()
                    
            return []
            
        except Exception:
            return []
    
    @staticmethod
    def _create_pos_order_from_ecommerce(platform, order_data):
        """
        Create a POS order from e-commerce order data
        """
        from .models import Customer, Sale, SaleLine, Product
        from django.contrib.auth.models import User
        from django.db import transaction
        
        try:
            with transaction.atomic():
                # Create or get customer from e-commerce order
                customer_email = order_data.get('customer', {}).get('email') or order_data.get('billing', {}).get('email')
                
                if customer_email:
                    customer, created = Customer.objects.get_or_create(
                        email=customer_email,
                        defaults={
                            'first_name': order_data.get('customer', {}).get('first_name') or order_data.get('billing', {}).get('first_name', 'Unknown'),
                            'last_name': order_data.get('customer', {}).get('last_name') or order_data.get('billing', {}).get('last_name', 'Customer'),
                            'phone': order_data.get('customer', {}).get('phone') or order_data.get('billing', {}).get('phone', '')
                        }
                    )
                else:
                    customer = None
                
                # Get a default cashier (system user)
                cashier = User.objects.filter(is_staff=True).first() or User.objects.first()
                
                # Get default warehouse for e-commerce sync
                from .models import Warehouse
                warehouse = Warehouse.objects.first()  # Default to first warehouse
                
                # Create the sale
                sale = Sale.objects.create(
                    receipt_number=f"ECOM-{order_data.get('id', 'N/A')}",
                    cashier=cashier,
                    customer=customer,
                    warehouse=warehouse,
                    total_amount=order_data.get('total_price', 0),
                    payment_status='completed',  # Assuming completed orders from e-commerce
                    sale_date=order_data.get('created_at', timezone.now()),
                    notes=f"Order from {platform.platform}: {order_data.get('order_number', 'N/A')}"
                )
                
                # Process line items
                line_items = order_data.get('line_items', [])
                for item in line_items:
                    sku = item.get('sku')
                    quantity = item.get('quantity', 1)
                    price = float(item.get('price', 0))
                    
                    # Find the corresponding product in our system
                    try:
                        product = Product.objects.get(sku=sku)
                    except Product.DoesNotExist:
                        # If product doesn't exist, we might want to create it or skip
                        continue
                    
                    # Create sale line
                    SaleLine.objects.create(
                        sale=sale,
                        product=product,
                        quantity=quantity,
                        unit_price=price,
                        total_price=quantity * price
                    )
                
                return True
                
        except Exception:
            return False