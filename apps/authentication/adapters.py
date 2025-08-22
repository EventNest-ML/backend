# apps/authentication/adapters.py
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
        print("Populate User: ", user)
        # Extract additional data from social provider
        if sociallogin.account.provider == 'google':
            user.firstname = data.get('first_name', '')
            user.lastname = data.get('last_name', '')
            # Keep user inactive to trigger Djoser's activation flow
            user.is_active = True
            
        elif sociallogin.account.provider == 'facebook':
            user.first_name = data.get('first_name', '')
            user.last_name = data.get('last_name', '')
            user.is_active = True
            
        return user
    
    def save_user(self, request, sociallogin, form=None):
        """
        Save the social user and trigger Djoser's activation flow
        """
        user = super().save_user(request, sociallogin, form)
        print("Saving user", user)
        
        # Check if this is a new user (first time social login)
        if not user.is_active:
            # Trigger Djoser's activation email
            self.trigger_djoser_activation(user)
        
        return user

    def trigger_djoser_activation(self, user):
        """
        Trigger Djoser's activation email for social users
        """
        try:
            # Import Djoser's email class
            from djoser.email import ActivationEmail
            from djoser.conf import settings as djoser_settings
            
            # Create the activation email using your configured template
            email = ActivationEmail(None, {})
            
            # Set up the context (same as Djoser does internally)
            context = email.get_context_data()
            context['user'] = user
            
            # Use Djoser's utils to generate uid and token
            from djoser.utils import encode_uid
            from django.contrib.auth.tokens import default_token_generator
            
            context['uid'] = encode_uid(user.pk)
            context['token'] = default_token_generator.make_token(user)
            context['url'] = f"{djoser_settings.ACTIVATION_URL.format(**context)}"
            
            # Send the email using Djoser's configured email class
            email.context = context
            email.send([user.email])
            
        except Exception as e:
            # Log error but don't break the flow
            print(f"Failed to send Djoser activation email: {e}")
    
    def is_auto_signup_allowed(self, request, sociallogin):
        """
        Control whether social signup is allowed
        """
        return True