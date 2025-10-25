import json
from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser
from rest_framework_simplejwt.tokens import AccessToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from django.contrib.auth import get_user_model

User = get_user_model()

@database_sync_to_async
def get_user_from_token(token_key):
    """
    Get user from JWT token
    """
    try:
        token = AccessToken(token_key)
        user_id = token.payload.get('user_id')
        if user_id:
            return User.objects.get(id=user_id)
    except (InvalidToken, TokenError, User.DoesNotExist) as e:
        print(f"JWT authentication error: {e}")
        return AnonymousUser()
    return AnonymousUser()

class JWTAuthMiddleware(BaseMiddleware):
    """
    JWT authentication middleware for Django Channels
    """
    
    async def __call__(self, scope, receive, send):
        # Extract token from query string
        query_string = scope.get('query_string', b'').decode()
        token = None
        
        # Parse query string for token
        if 'token=' in query_string:
            token = query_string.split('token=')[1].split('&')[0]
        
        # If no token in query string, check headers
        if not token:
            headers = dict(scope['headers'])
            if b'authorization' in headers:
                auth_header = headers[b'authorization'].decode()
                if auth_header.startswith('Bearer '):
                    token = auth_header[7:]
        
        # Authenticate user
        if token:
            scope['user'] = await get_user_from_token(token)
        else:
            scope['user'] = AnonymousUser()
        
        return await super().__call__(scope, receive, send)