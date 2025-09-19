from django.shortcuts import render
from rest_framework import generics, permissions
from drf_yasg.utils import swagger_auto_schema

from .models import Contact
from .serializers import ContactSerializer
# Create your views here.




class ContactListCreateAPIView(generics.ListCreateAPIView):
    """
    GET: List all saved contacts of the logged-in user
    POST: Create a new saved contact
    """
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Contact.objects.filter(owner=self.request.user)
    
    @swagger_auto_schema(
        operation_description="Retrieve all saved contacts belonging to the logged-in user.",
        operation_summary="List Saved Contacts",
        responses={200: ContactSerializer(many=True)}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)
    
    @swagger_auto_schema(
        operation_description="Create a new contact and assign it to the logged-in user.",
        operation_summary="Create Contact",
        request_body=ContactSerializer,
        responses={201: ContactSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class ContactRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET: Retrieve a contact by ID  
    PUT: Update a contact  
    DELETE: Remove a contact  
    """
    serializer_class = ContactSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Prevent errors during Swagger schema generation
        if getattr(self, "swagger_fake_view", False) or not self.request.user.is_authenticated:
            return Contact.objects.none()
        return Contact.objects.filter(owner=self.request.user)

    @swagger_auto_schema(
        operation_summary="Retrieve a Contact",
        operation_description="Retrieve a single saved contact by its ID, only if it belongs to the logged-in user.",
        responses={200: ContactSerializer}
    )
    def get(self, request, *args, **kwargs):
        return super().get(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Update a Contact",
        operation_description="Update an existing contact. Only the owner can perform this action.",
        request_body=ContactSerializer,
        responses={200: ContactSerializer}
    )
    def put(self, request, *args, **kwargs):
        return super().put(request, *args, **kwargs)

    @swagger_auto_schema(
        operation_summary="Partially Update a Contact",
        operation_description="Partially update an existing contact (only the provided fields will be updated).",
        request_body=ContactSerializer,
        responses={200: ContactSerializer}
    )
    def patch(self, request, *args, **kwargs):
        return super().patch(request, *args, **kwargs)
    

    @swagger_auto_schema(
        operation_summary="Delete a Contact",
        operation_description="Delete a contact by ID. Only the owner can delete their contacts.",
        responses={204: "Contact deleted successfully"}
    )
    def delete(self, request, *args, **kwargs):
        return super().delete(request, *args, **kwargs)