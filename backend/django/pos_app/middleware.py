from django.http import JsonResponse
from rest_framework_simplejwt.tokens import AccessToken
from .models import BlacklistedToken

class TokenBlacklistMiddleware:
    """
    Middleware to check if a JWT token has been blacklisted.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        self.excluded_paths = [
            '/api/v1/token/', '/api/v1/register/', '/api/v1/password-reset/',
            '/api/v1/password-reset-confirm/', '/api/v1/password-reset-validate/'
        ]

    def __call__(self, request):
        # Skip token validation for excluded paths
        if request.path in self.excluded_paths or request.path.startswith('/api/v1/mfa/verify/'):
            response = self.get_response(request)
            return response

        # Check for JWT token in Authorization header
        auth_header = request.META.get('HTTP_AUTHORIZATION')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]
            
            try:
                # Decode the token to get the jti
                access_token = AccessToken(token)
                jti = str(access_token['jti'])
                
                # Check if token is blacklisted
                if self.is_token_blacklisted(jti):
                    return JsonResponse(
                        {'detail': 'Token has been revoked', 'code': 'token_revoked'}, 
                        status=401
                    )
            except Exception:
                # If token is invalid, let the default JWT auth handle it
                pass

        response = self.get_response(request)
        return response

    def is_token_blacklisted(self, jti):
        return BlacklistedToken.objects.filter(jti=jti).exists()
