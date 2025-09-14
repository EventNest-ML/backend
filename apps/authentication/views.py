from django.contrib.auth import get_user_model
from rest_framework.response import Response
from rest_framework import status
from rest_framework import status
from djoser.views import UserViewSet
from djoser.email import ActivationEmail
from rest_framework.decorators import action
from .serializers import CustomResendActivationSerializer
from django.contrib.auth.tokens import default_token_generator
from djoser.views import UserViewSet
from rest_framework.response import Response
from rest_framework import status
from .serializers import CustomResendActivationSerializer
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from .serializers import CustomResendActivationSerializer
from rest_framework.permissions import AllowAny

User = get_user_model()


class CustomUserViewSet(UserViewSet):
    def get_serializer_class(self):
        print("Getting Serializer...")
        if self.action == 'resend_activation':
            return CustomResendActivationSerializer
        return super().get_serializer_class()

    def resend_activation(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        uidb64 = self.encode_uid(user.pk)
        token = default_token_generator.make_token(user)

        context = {
            "user": user,
            "uid": uidb64,
            "token": token,
        }
        ActivationEmail(context).send(to=[user.email])

        return Response({"detail": "Activation link resent"}, status=status.HTTP_200_OK)
        



class CustomResendActivationView(APIView):
    """
    Resend activation email using email or UID
    """
    permission_classes = [AllowAny]
    @swagger_auto_schema(
        operation_description="Resend activation email using email or UID",
        request_body=CustomResendActivationSerializer,
        responses={
            204: openapi.Response(
                description="Activation email sent successfully"
            ),
            400: openapi.Response(
                description="Bad request - validation errors"
            )
        },
        tags=['Authentication']
    )
    def post(self, request):
        serializer = CustomResendActivationSerializer(
            data=request.data, 
            context={'request': request}
        )
        
        if serializer.is_valid():
            serializer.save()
            return Response(
                {"detail": "Activation email sent successfully."}, 
                status=status.HTTP_204_NO_CONTENT
            )
        
        return Response(
            serializer.errors, 
            status=status.HTTP_400_BAD_REQUEST
        )

