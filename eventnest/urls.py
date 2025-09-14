

from django.contrib import admin
from django.urls import path, include
from .swagger import schema_view




urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0),),
    path('accounts/', include('allauth.urls'), name='socials'),
    path('api/auth/users/', include('apps.authentication.urls'), name='users'),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    
    path("events/", include("apps.events.urls")), #urls for events
]


admin.site.site_header = "EventNest API"
admin.site.site_title = "EventNest API Management Portal"
admin.site.index_title = "Welcome to the EventNest Admin Portal"