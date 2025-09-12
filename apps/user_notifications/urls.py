from django.urls import path
from . import views


urlpatterns = [
    path('', views.NotificationAPIView.as_view(), name='notifications'),
    path('<int:pk>/', views.NotificationDetailAPIView.as_view(), name='notification_detail'),
    path('count/', views.NotificationCountAPIView.as_view(), name='count'),
]


