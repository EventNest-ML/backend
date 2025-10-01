from pathlib import Path
import environ
from decouple import config
from celery.schedules import crontab

env = environ.Env(
    DEBUG=(bool, False)
)

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent

# Application definition
DJANGO_APPS = [
    'daphne',
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
]

THIRD_PARTY_APPS = [
    'rest_framework',
    'drf_yasg',
    'django_filters',
    'phonenumber_field',
    'djoser',
    'rest_framework_simplejwt',
    'rest_framework_simplejwt.token_blacklist',
    'corsheaders',
    
    # Django-allauth for social authentication
    'allauth',
    'allauth.account',
    'allauth.socialaccount',
    'allauth.socialaccount.providers.google',
    # 'allauth.socialaccount.providers.facebook',
    'djcelery_email',
    'django_celery_beat',
    'notifications',
    'channels',
    'djmoney',
    'imagekit',
]


LOCAL_APPS = [
    'apps.budgets',
    'apps.events',
    'apps.authentication',
    'apps.tasks',
    'apps.contacts',
    'apps.user_notifications',
]

INSTALLED_APPS = DJANGO_APPS + THIRD_PARTY_APPS + LOCAL_APPS

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
]

ROOT_URLCONF = "eventnest.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        'DIRS': [BASE_DIR / 'templates'],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

ASGI_APPLICATION = "eventnest.asgi.application"

# Database
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]

# Internationalization
LANGUAGE_CODE = "en-us"
# TIME_ZONE = "UTC"
TIME_ZONE = 'Africa/Lagos'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

AUTH_USER_MODEL = 'authentication.User'

ACCOUNT_ADAPTER = 'apps.authentication.adapters.CustomAccountAdapter'
SOCIALACCOUNT_ADAPTER = 'apps.authentication.adapters.CustomSocialAccountAdapter'

# Sites framework
SITE_ID = 1

# ============== REST FRAMEWORK CONFIGURATION ==============
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_RENDERER_CLASSES': [
        # 'rest_framework.renderers.BrowsableAPIRenderer',
        'rest_framework.renderers.JSONRenderer',
    ],
}

# ============== JWT CONFIGURATION ==============
from datetime import timedelta

SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=7),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': config('SECRET_KEY'),
    'AUTH_HEADER_TYPES': ('JWT', 'Bearer'),
}

# ============== DJOSER CONFIGURATION ==============
DJOSER = {
    'LOGIN_FIELD': 'email',
    'USER_CREATE_PASSWORD_RETYPE': True,
    'USERNAME_CHANGED_EMAIL_CONFIRMATION': True,
    'PASSWORD_CHANGED_EMAIL_CONFIRMATION': True,
    'SEND_CONFIRMATION_EMAIL': True,
    'SEND_ACTIVATION_EMAIL': True,
    'SET_PASSWORD_RETYPE': True,
    'PASSWORD_RESET_CONFIRM_URL': 'password-reset?uid={uid}&token={token}',
    'USERNAME_RESET_CONFIRM_URL': 'username-reset?uid={uid}&token={token}',
    'ACTIVATION_URL': 'activate?uid={uid}&token={token}',
    'SERIALIZERS': {
        'user_create': 'apps.authentication.serializers.CustomUserCreateSerializer',
        'user': 'apps.authentication.serializers.CustomUserSerializer',
        'current_user': 'apps.authentication.serializers.CustomUserSerializer',
        'user_delete': 'djoser.serializers.UserDeleteSerializer',
        'set_password': 'djoser.serializers.SetPasswordSerializer',
        'password_reset': 'djoser.serializers.SendEmailResetSerializer',
        'password_reset_confirm': 'djoser.serializers.PasswordResetConfirmSerializer',
        'set_username': 'djoser.serializers.SetUsernameSerializer',
        'username_reset': 'djoser.serializers.SendEmailResetSerializer',
        'username_reset_confirm': 'djoser.serializers.UsernameResetConfirmSerializer',
        'activation': 'djoser.serializers.ActivationSerializer',
    },
    'EMAIL': {
        'activation': 'apps.authentication.email.ActivationEmail',
        'confirmation': 'apps.authentication.email.ConfirmationEmail',
        'password_reset': 'apps.authentication.email.PasswordResetEmail',
        'password_changed_confirmation': 'apps.authentication.email.PasswordChangedConfirmationEmail',
        'username_changed_confirmation': 'apps.authentication.email.UsernameChangedConfirmationEmail',
        'username_reset': 'apps.authentication.email.UsernameResetEmail',
    },
    'CONSTANTS': {
        'messages': 'apps.authentication.constants.Messages',
    },
}


# ============== DJANGO-ALLAUTH CONFIGURATION ==============
AUTHENTICATION_BACKENDS = [
    'django.contrib.auth.backends.ModelBackend',
    'allauth.account.auth_backends.AuthenticationBackend',
]

# Account settings (updated for newer versions)
ACCOUNT_LOGIN_METHODS = {'email'}  # Replaces ACCOUNT_AUTHENTICATION_METHOD
ACCOUNT_SIGNUP_FIELDS = ['email*', 'password1*', 'password2*']  # Replaces EMAIL_REQUIRED and USERNAME_REQUIRED
ACCOUNT_EMAIL_VERIFICATION = 'none'
ACCOUNT_UNIQUE_EMAIL = True
ACCOUNT_LOGIN_ON_EMAIL_CONFIRMATION = False
ACCOUNT_LOGOUT_ON_GET = True

# Tell Allauth to use email as the username field
ACCOUNT_USER_MODEL_USERNAME_FIELD = 'email'
ACCOUNT_USERNAME_MIN_LENGTH = 1


# Social account settings
SOCIALACCOUNT_AUTO_SIGNUP = True
SOCIALACCOUNT_EMAIL_VERIFICATION = 'none'  # Require email verification for social accounts
SOCIALACCOUNT_LOGIN_ON_GET = True
SOCIALACCOUNT_STORE_TOKENS = True

# ACCOUNT_SIGNUP_REDIRECT_URL = 'http://localhost:3000/login'

# Provider configurations
SOCIALACCOUNT_PROVIDERS = {
    'google': {
        'APP': {
            'client_id': config('GOOGLE_OAUTH2_CLIENT_ID', default=''),
            'secret': config('GOOGLE_OAUTH2_CLIENT_SECRET', default=''),
            'key': ''
        },
        'SCOPE': [
            'profile',
            'email',
        ],
        'AUTH_PARAMS': {
            'access_type': 'online',
        }
    },
    # 'facebook': {
    #     'APP': {
    #         'client_id': config('FACEBOOK_APP_ID', default=''),
    #         'secret': config('FACEBOOK_APP_SECRET', default=''),
    #         'key': ''
    #     },
    #     'METHOD': 'oauth2',
    #     'SDK_URL': '//connect.facebook.net/{locale}/sdk.js',
    #     'SCOPE': ['email', 'public_profile'],
    #     'AUTH_PARAMS': {'auth_type': 'reauthenticate'},
    #     'INIT_PARAMS': {'cookie': True},
    #     'FIELDS': [
    #         'id',
    #         'first_name',
    #         'last_name',
    #         'name',
    #         'email',
    #         'picture.type(large)',
    #     ],
    #     'EXCHANGE_TOKEN': True,
    #     'VERIFIED_EMAIL': False,
    #     'VERSION': 'v18.0',
    # }
}

# Redirect URLs (for testing without frontend)
# LOGIN_REDIRECT_URL = '/accounts/profile/'  # Django admin or custom success page
# LOGOUT_REDIRECT_URL = '/accounts/login/'
SOCIALACCOUNT_LOGIN_ON_GET = True

# Alternative: redirect to admin for testing
# LOGIN_REDIRECT_URL = '/admin/'

# Custom signals for JWT token creation on social login
SOCIALACCOUNT_SIGNALS = {
    'allauth.socialaccount.signals.pre_social_login': 'apps.authentication.signals.pre_social_login',
    'allauth.socialaccount.signals.social_account_added': 'apps.authentication.signals.social_account_added',
}

# ============== CORS CONFIGURATION ==============
CORS_ALLOWED_ORIGINS = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:5500",
    "http://127.0.0.1:5500",
]
CORS_ALLOW_CREDENTIALS = True


# Frontend URL for email templates
FRONTEND_URL = config('FRONTEND_URL', default='http://localhost:3000')

CELERY_BROKER_URL = config('CELERY_BROKER_URL')
CELERY_RESULT_BACKEND = config('CELERY_RESULT_BACKEND')
CELERY_TIMEZONE = "UTC"

EMAIL_BACKEND = config('EMAIL_BACKEND')


SWAGGER_SETTINGS = {
    'SECURITY_DEFINITIONS': {
        'Bearer': {
            'type': 'apiKey',
            'name': 'Authorization',
            'in': 'header',
            'description': 'JWT authorization header using the Bearer scheme. Example: "Bearer {token}"'
        }
    },
    'USE_SESSION_AUTH': False,
}


CELERY_BEAT_SCHEDULE = {
    'send-due-reminders': {
        'task': 'apps.user_notifications.tasks.send_due_reminders',
        'schedule': crontab(minute=0, hour='*'),
    },
}
