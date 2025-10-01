from .base import *
import environ

env = environ.Env()
environ.Env.read_env(BASE_DIR / '.env.production')

# Security
SECRET_KEY = env("SECRET_KEY")
ALLOWED_HOSTS = env("ALLOWED_HOSTS").split(" ")
DEBUG = env.bool('DEBUG', default=False)

# Google Cloud Storage Configuration
DEFAULT_FILE_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
STATICFILES_STORAGE = 'storages.backends.gcloud.GoogleCloudStorage'
GS_BUCKET_NAME = env('GS_BUCKET_NAME')
GS_PROJECT_ID = env('GS_PROJECT_ID')
GS_DEFAULT_ACL = 'publicRead'  # Make static files publicly accessible
GS_QUERYSTRING_AUTH = False  # Serve static files without signed URLs
GS_FILE_OVERWRITE = False  # Prevent overwriting files with the same name

# Static Files
STATIC_URL = f"https://storage.googleapis.com/{env('GS_BUCKET_NAME')}/static/"
# STATIC_ROOT is not needed for GCS, but keep for collectstatic locally if needed
# STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = []  # Adjust if you have local static directories for development

# Media Files
MEDIA_URL = f"https://storage.googleapis.com/{env('GS_BUCKET_NAME')}/media/"

# Installed Apps
INSTALLED_APPS += ['storages']

# Email Configuration
EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env.int('EMAIL_PORT')
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
DOMAIN = env('DOMAIN')
SITE_NAME = 'EventNest'

# Database Configuration
DATABASES = {
    'default': {
        'ENGINE': env('POSTGRES_ENGINE'),
        'NAME': env('POSTGRES_DBNAME'),
        'USER': env('POSTGRES_USER'),
        'PASSWORD': env('POSTGRES_PASSWORD'),
        'HOST': env('POSTGRES_HOST'),
        'PORT': env('POSTGRES_PORT'),
    }
}

# Celery and Redis Configuration
CELERY_REDIS_BACKEND_USE_SSL = {
    'ssl_cert_reqs': 'optional',
}
REDIS_HOST = env('REDIS_HOST')
REDIS_PORT = env('REDIS_PORT')

# Channels Configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [(REDIS_HOST, REDIS_PORT)],
        },
    },
}