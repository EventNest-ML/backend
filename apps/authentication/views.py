import boto3
from django.contrib.auth import get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.conf import settings
from .authentication import CognitoJWTAuthentication

User = get_user_model()

# AWS Cognito Client
# cognito_client = boto3.client("cognito-idp", region_name=settings.AWS_COGNITO_REGION)

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from djoser.views import UserViewSet as DjoserUserViewSet
import boto3
from django.conf import settings

class PasswordResetConfirmView(APIView):
    def post(self, request, *args, **kwargs):
        # First, call Djoser's password reset confirm endpoint
        # You can do this by forwarding the request to Djoser's view
        djoser_response = self.forward_to_djoser(request)
        
        if djoser_response.status_code == status.HTTP_204_NO_CONTENT:
            # Django password was successfully reset, now reset in Cognito
            uid = request.data.get('uid')
            new_password = request.data.get('new_password')
            
            try:
                # Get user from Django
                User = get_user_model()
                user = User.objects.get(pk=uid)
                
                # Reset password in Cognito
                # self.reset_cognito_password(user.username, new_password)
                
                return djoser_response
            except User.DoesNotExist:
                return Response(
                    {"detail": "User not found."}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            except Exception as e:
                return Response(
                    {"detail": f"Error resetting Cognito password: {str(e)}"}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
        else:
            # If Djoser validation failed, return its response
            return djoser_response
    
    def forward_to_djoser(self, request):
        # Create an instance of Djoser's UserViewSet
        viewset = DjoserUserViewSet.as_view({'post': 'reset_password_confirm'})
        # Forward the request and get the response
        response = viewset(request._request)
        return response
    
    def reset_cognito_password(self, username, new_password):
        client = boto3.client('cognito-idp', region_name=settings.COGNITO_AWS_REGION)
        
        # Find user in Cognito by username
        response = client.list_users(
            UserPoolId=settings.COGNITO_USER_POOL_ID,
            Filter=f'username = "{username}"',
            Limit=1
        )
        
        if response['Users']:
            cognito_username = response['Users'][0]['Username']
            
            # Reset password
            client.admin_set_user_password(
                UserPoolId=settings.COGNITO_USER_POOL_ID,
                Username=cognito_username,
                Password=new_password,
                Permanent=True
            )
        else:
            raise Exception(f"User {username} not found in Cognito")

class CognitoLoginView(APIView):
    def post(self, request):
        print(request)
        email = request.data.get("email")
        password = request.data.get("password")

        print({
            'email': email,
            'password': password,
            'client_id': settings.AWS_COGNITO_CLIENT_ID
        })


        if not email or not password:
            return Response({"error": "Email and password are required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            # Authenticate user in Cognito
            auth_result = cognito_client.initiate_auth(
                ClientId=settings.AWS_COGNITO_CLIENT_ID,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": email, "PASSWORD": password},
            )
            print(auth_result)
            # Get Cognito tokens
            access_token = auth_result["AuthenticationResult"]["AccessToken"]
            refresh_token = auth_result["AuthenticationResult"]["RefreshToken"]
            id_token = auth_result['AuthenticationResult']['IdToken']
            expires_in = auth_result['AuthenticationResult']['ExpiresIn']

            # Create or fetch the user in Django
            user, created = User.objects.get_or_create(email=email)

            # # Generate JWT using SimpleJWT
            # jwt_refresh = RefreshToken.for_user(user)

            return Response({
                "access_token": str(access_token),
                "refresh_token": str(refresh_token),
                "id_token": str(id_token),
                "expires_in": expires_in
            })
        
        except cognito_client.exceptions.NotAuthorizedException:
            return Response({"error": "Invalid email or password"}, status=status.HTTP_401_UNAUTHORIZED)

        except cognito_client.exceptions.UserNotFoundException:
            return Response({"error": "User does not exist"}, status=status.HTTP_404_NOT_FOUND)
        




class ProtectedView(APIView):
    # authentication_classes = [CognitoJWTAuthentication]
    # permission_classes = [IsAuthenticated]

    def get(self, request):
        print(request.user)

        return Response({"message": "Authenticated successfully!"})

