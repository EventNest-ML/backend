from django.urls import path
from .views import CustomResendActivationView


app_name = "auth"

urlpatterns = [
    path('resend_activation/', CustomResendActivationView.as_view(), name='resend_activation'),
]
