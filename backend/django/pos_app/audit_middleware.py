import json
import logging
import re
from django.utils import timezone
from .models import AuditLog
from django.contrib.auth.models import User
from .signals import set_current_user

logger = logging.getLogger(__name__)

class AuditMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.auditable_endpoints = [
            '/api/v1/products/', '/api/v1/customers/', '/api/v1/sales/',
            '/api/v1/inventory/', '/api/v1/transfers/', '/api/v1/categories/',
            '/api/v1/warehouses/', '/api/v1/locations/', '/api/v1/bins/',
            '/api/v1/returns/', '/api/v1/promotions/', '/api/v1/coupons/',
            '/api/v1/purchase-orders/', '/api/v1/grns/', '/api/v1/users/',
        ]
        self.audit_methods = ['POST', 'PUT', 'PATCH', 'DELETE']

    def __call__(self, request):
        set_current_user(getattr(request, 'user', None))

        request._audit_original_data = {}
        if request.method in self.audit_methods and request.body:
            content_type = request.META.get('CONTENT_TYPE', '').lower()
            if 'application/json' in content_type:
                try:
                    request._audit_original_data = json.loads(request.body)
                except json.JSONDecodeError:
                    # Log the error but continue processing
                    logger.warning(f"JSONDecodeError for request body with Content-Type: {content_type}")
                    pass
            elif 'multipart/form-data' in content_type:
                # For file uploads, we don't try to parse the body as JSON
                # We can store a placeholder or relevant metadata if needed
                request._audit_original_data = {'_note': 'Multipart form data (file upload) - body not parsed as JSON'}
            else:
                # For other content types, store the raw body or a placeholder
                request._audit_original_data = {'_note': f'Request body not parsed as JSON (Content-Type: {content_type})'}

        response = self.get_response(request)

        user = getattr(request, 'user', None)
        if user and user.is_authenticated:
            if any(endpoint in request.path for endpoint in self.auditable_endpoints):
                action = self._get_action_from_method(request.method, response.status_code)
                if action:
                    object_type = self._get_object_type_from_path(request.path)
                    if object_type:
                        object_id = self._get_object_id_from_path(request.path, object_type)
                        self._create_audit_log(request, action, object_type, object_id)

            if '/api/v1/token/' in request.path and request.method == 'POST' and response.status_code == 200:
                self._create_login_audit_log(request, 'login')
            if '/api/v1/logout/' in request.path and request.method == 'POST':
                self._create_login_audit_log(request, 'logout')

        return response

    def _get_action_from_method(self, method, status_code):
        method_to_action = {'POST': 'create', 'PUT': 'update', 'PATCH': 'update', 'DELETE': 'delete'}
        if method in method_to_action and 200 <= status_code < 300:
            return method_to_action[method]
        return None

    def _get_object_type_from_path(self, path):
        path_mapping = {
            'products': 'product', 'customers': 'customer', 'sales': 'sale',
            'inventory': 'inventory', 'transfers': 'transfer', 'categories': 'category',
            'warehouses': 'warehouse', 'locations': 'location', 'bins': 'bin',
            'returns': 'return', 'promotions': 'promotion', 'coupons': 'coupon',
            'purchase-orders': 'purchaseorder', 'grns': 'goodsreceivednote', 'users': 'user',
        }
        for path_segment, object_type in path_mapping.items():
            if f'/{path_segment}/' in path or path.endswith(f'/{path_segment}'):
                return object_type
        return None

    def _get_object_id_from_path(self, path, object_type):
        pattern = rf'/api/v1/{object_type}s/(\d+)/'
        match = re.search(pattern, path)
        return int(match.group(1)) if match else None

    def _create_audit_log(self, request, action, object_type, object_id):
        try:
            old_values, new_values = None, None
            if action == 'update':
                new_values = getattr(request, '_audit_original_data', {})
            elif action == 'create':
                new_values = getattr(request, '_audit_original_data', {})
            elif action == 'delete':
                old_values = getattr(request, '_audit_original_data', {})
            
            object_repr = f"{object_type.title()} operation" + (f" (ID: {object_id})" if object_id else "")
            
            AuditLog.objects.create(
                user=request.user, action=action, object_type=object_type,
                object_id=object_id or 0, object_repr=object_repr,
                old_values=old_values, new_values=new_values, timestamp=timezone.now(),
                ip_address=self._get_client_ip(request), user_agent=request.META.get('HTTP_USER_AGENT', ''),
                notes=f"{action.title()} {object_type} via API"
            )
        except Exception as e:
            logger.error(f"Failed to create audit log: {str(e)}")

    def _create_login_audit_log(self, request, action):
        try:
            user = request.user
            if action == 'login':
                try:
                    request_data = json.loads(request.body)
                    username_or_email = request_data.get('username', '')
                    user = User.objects.filter(email=username_or_email).first() or User.objects.filter(username=username_or_email).first()
                except:
                    user = None
            
            if user:
                AuditLog.objects.create(
                    user=user, action=action, object_type='session', object_id=user.id,
                    object_repr=f"User {user.username} {action}", timestamp=timezone.now(),
                    ip_address=self._get_client_ip(request), user_agent=request.META.get('HTTP_USER_AGENT', ''),
                    notes=f"User {action} from IP {self._get_client_ip(request)}"
                )
        except Exception as e:
            logger.error(f"Failed to create login audit log: {str(e)}")

    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class StockChangeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if 200 <= response.status_code < 300:
            if request.path.startswith('/api/v1/sales/') and request.method in ['POST', 'PUT', 'PATCH']:
                self._log_stock_change_for_sale(request)
            elif request.path.startswith('/api/v1/transfers/') and request.method in ['POST', 'PUT', 'PATCH']:
                self._log_stock_change_for_transfer(request)
            elif request.path.startswith('/api/v1/returns/') and request.method in ['POST', 'PUT', 'PATCH']:
                self._log_stock_change_for_return(request)
        return response

    def _log_stock_change_for_sale(self, request):
        pass

    def _log_stock_change_for_transfer(self, request):
        pass

    def _log_stock_change_for_return(self, request):
        pass
