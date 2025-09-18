from django.urls import path
from .views import (
    EventListCreateAPIView,
    EventDetailAPIView,
    InvitationCreateAPIView,
    InvitationRespondAPIView,
    InvitationRetrieveAPIView,
    CollaboratorListAPIView, 
    CollaboratorDetailAPIView
)

urlpatterns = [
    # Event URLs
    
    path('', EventListCreateAPIView.as_view(), name='event-list-create'),
    path('<uuid:id>/', EventDetailAPIView.as_view(), name='event-detail'),
    
    # Invitation URLs
    path('<uuid:id>/invite/', InvitationCreateAPIView.as_view(), name='event-invite'),
    path("invites/respond/", InvitationRespondAPIView.as_view(), name="invitation-respond"),  # accepts or declines
    path("invites/validate/", InvitationRetrieveAPIView.as_view(), name="invitation-retrieve"),  # fetch info

    #Collabotator urls
    path("<uuid:event_id>/contributors/", CollaboratorListAPIView.as_view(), name="contributor-list"),
    path("<uuid:event_id>/collabotator/<int:pk>/", CollaboratorDetailAPIView.as_view(), name="collabotator-detail"),
    
    

]