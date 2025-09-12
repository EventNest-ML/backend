from .base import *

environ.Env.read_env(BASE_DIR / '.env')

SECRET_KEY = env("SECRET_KEY")


ALLOWED_HOSTS = []#env("ALLOWED_HOSTS").split(" ")

DEBUG = True

EMAIL_HOST = env('EMAIL_HOST')
EMAIL_PORT = env('EMAIL_PORT')
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = env('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = env('DEFAULT_FROM_EMAIL')
DOMAIN = env('DOMAIN')
SITE_NAME = 'EventNest Development'


STATIC_URL = "/staticfiles/"
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIR = []

MEDIA_URL = '/mediafiles/'
MEDIA_ROOT = BASE_DIR / 'mediafiles'

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


CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels.layers.InMemoryChannelLayer'
    }
}
