from django.urls import path
from .views import (
    EventListCreateAPIView,
    EventDetailAPIView,
    InvitationCreateAPIView,
    InvitationAcceptAPIView,
)

urlpatterns = [
    # Event URLs
    path('', EventListCreateAPIView.as_view(), name='event-list-create'),
    path('<uuid:id>/', EventDetailAPIView.as_view(), name='event-detail'),
    
    # Invitation URLs
    path('<uuid:id>/invite/', InvitationCreateAPIView.as_view(), name='event-invite'),
    path('invites/accept/', InvitationAcceptAPIView.as_view(), name='invitation-accept'),
]