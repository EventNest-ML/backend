from django.dispatch import receiver
from allauth.socialaccount.signals import pre_social_login, social_account_added
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model

User = get_user_model()

@receiver(pre_social_login)
def pre_social_login_handler(sender, request, sociallogin, **kwargs):
    """
    Handle pre-social login events
    """
    user = sociallogin.user
    
    # You can add custom logic here
    # e.g., check if user should be allowed to login
    pass

@receiver(social_account_added)
def social_account_added_handler(sender, request, sociallogin, **kwargs):
    """
    Handle social account addition
    """
    user = sociallogin.user
    
    # Generate JWT tokens for the user
    refresh = RefreshToken.for_user(user)
    access_token = refresh.access_token
    
    # Store tokens in session or return them
    request.session['access_token'] = str(access_token)
    request.session['refresh_token'] = str(refresh)