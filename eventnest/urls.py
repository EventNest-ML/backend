

from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse
from .swagger import schema_view
from django.contrib.auth.decorators import login_required

@login_required
def social_login_success(request):
    return JsonResponse({
        'success': True,
        'user': {
            'id': request.user.id,
            'email': request.user.email,
            'first_name': request.user.firstname,
            'last_name': request.user.lastname,
        },
        'message': 'Social login successful!'
    })

urlpatterns = [
    path('admin/', admin.site.urls),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0),),
    path('accounts/', include('allauth.urls'), name='socials'),
    path('api/auth/', include('djoser.urls')),
    path('api/auth/', include('djoser.urls.jwt')),
    path('accounts/profile/', social_login_success, name='social_login_success'),
]


admin.site.site_header = "EventNest API"
admin.site.site_title = "EventNest API Management Portal"
admin.site.index_title = "Welcome to the EventNest Admin Portal"