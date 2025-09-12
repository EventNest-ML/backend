from channels.middleware import BaseMiddleware
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import UntypedToken
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from jwt import decode as jwt_decode
from django.conf import settings
import json

User = get_user_model()

class JWTAuthMiddleware(BaseMiddleware):
    """
    Custom middleware for JWT authentication in WebSocket
    """
    
    async def __call__(self, scope, receive, send):
        headers = dict(scope['headers'])
        
        # Look for Authorization header
        if b'authorization' in headers:
            try:
                auth_header = headers[b'authorization'].decode()
                if auth_header.startswith('Bearer '):
                    token = auth_header.split('Bearer ')[1]
                    scope['user'] = await self.get_user_from_jwt(token)
                else:
                    scope['user'] = AnonymousUser()
            except Exception as e:
                print(f"JWT Auth error: {e}")
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()
            
        return await super().__call__(scope, receive, send)
    
    @database_sync_to_async
    def get_user_from_jwt(self, token):
        try:
            # Validate token
            UntypedToken(token)
            
            # Decode token to get user info
            decoded_data = jwt_decode(
                token, 
                settings.SECRET_KEY, 
                algorithms=["HS256"]
            )
            
            user = User.objects.get(id=decoded_data['user_id'])
            return user
        except (InvalidToken, TokenError, User.DoesNotExist) as e:
            print(f"JWT validation error: {e}")
            return AnonymousUser()