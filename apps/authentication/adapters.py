from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

User = get_user_model()

class CustomAccountAdapter(DefaultAccountAdapter):
    def save_user(self, request, user, form, commit=True):
        """
        Custom user creation logic for regular signup
        """
        user = super().save_user(request, user, form, commit=False)
        
        # Add any custom logic here
        if commit:
            user.save()
        return user

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        """
        Handle existing users with same email
        """
        print("Presocial login running")
        user = sociallogin.user
        if user.id:
            return
            
        if not user.email:
            return
            
        # Check if a user with this email already exists
        try:
            existing_user = User.objects.get(email=user.email)
            # Connect the social account to existing user
            sociallogin.connect(request, existing_user)
        except User.DoesNotExist:
            pass
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user instance with social account data
        """
        user = super().populate_user(request, sociallogin, data)
        
        # Extract additional data from social provider
        if sociallogin.account.provider == 'google':
            print("Google provider detected: ", data)
            user.first_name = data.get('first_name', '')
            user.last_name = data.get('last_name', '')
            user.is_verified = True  # Social accounts are pre-verified
            
        elif sociallogin.account.provider == 'facebook':
            user.first_name = data.get('first_name', '')
            user.last_name = data.get('last_name', '')
            user.is_verified = True
            
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save the social user
        """
        user = super().save_user(request, sociallogin, form)
        
        # Additional processing after user creation
        # e.g., send welcome email, create profile, etc.
        
        return user
