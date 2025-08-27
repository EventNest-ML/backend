from django.urls import path
from .views import EventListCreateAPIView, EventDetailUpdateDestroyAPIView

urlpatterns = [
    # map URLs to  views
    path('', EventListCreateAPIView.as_view(), name='event-list-create'),
    path('<int:pkid>/', EventDetailUpdateDestroyAPIView.as_view(), name='event-detail-update-destroy'),
]