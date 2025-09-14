# your_app/adapters.py
from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from django.conf import settings
from rest_framework_simplejwt.tokens import RefreshToken

class CustomAccountAdapter(DefaultAccountAdapter):
    def send_mail(self, template_prefix, email, context):
        # Prevent allauth from sending password reset / confirmation emails automatically
        return

    def _build_token_redirect(self, user):
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)
        return (
            f"{settings.FRONTEND_URL}/auth/callback?"
            f"access={access_token}&refresh={refresh_token}"
        )

    def get_login_redirect_url(self, request):
        """
        After login is successful
        """
        return self._build_token_redirect(request.user)

    def get_signup_redirect_url(self, request):
        """
        After *signup* is successful
        """
        return self._build_token_redirect(request.user)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):

        """
        Auto-link social accounts to existing users by email.
        """
        if sociallogin.is_existing:
            # Social account already linked → nothing to do
            return

        email = sociallogin.account.extra_data.get("email")
        print("SOCIALS: ", sociallogin, email)
        if not email:
            return

        User = get_user_model()
        try:
            # If user already exists with this email → link account
            user = User.objects.get(email=email)
            sociallogin.connect(request, user)

        except User.DoesNotExist:
            # New user → let the normal signup flow continue
            return
        
    def get_connect_redirect_url(self, request, socialaccount):
        print("Connect redirect url")
        """
        Called after a *new social signup* succeeds.
        Issue JWT tokens and redirect to frontend callback.
        """
        user = request.user
        refresh = RefreshToken.for_user(user)

        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return (
            f"{settings.FRONTEND_URL}/auth/callback?"
            f"access={access_token}&refresh={refresh_token}"
        )
    
    def populate_user(self, request, sociallogin, data):
        """
        Populate user fields (first_name, last_name, email) from Google data.
        """
        user = super().populate_user(request, sociallogin, data)
        extra_data = sociallogin.account.extra_data

        user.firstname = extra_data.get("given_name", "")
        user.lastname = extra_data.get("family_name", "")
        if not user.firstname and "name" in extra_data:
            parts = extra_data["name"].split(" ", 1)
            user.firstname = parts[0]
            if len(parts) > 1:
                user.lastname = parts[1]

        return user
