from django.urls import path
from .views import CustomResendActivationView


urlpatterns = [
    path('resend_activation/', CustomResendActivationView.as_view(), name='resend_activation'),
]
