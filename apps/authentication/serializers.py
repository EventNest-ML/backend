from django.contrib.auth import get_user_model
from django.contrib.auth import authenticate
from rest_framework import serializers
from djoser.serializers import UserCreateSerializer as DjoserUserCreateSerializer
import re

User = get_user_model()

class UserSerializer(serializers.ModelSerializer):

    firstname = serializers.SerializerMethodField()
    lastname = serializers.SerializerMethodField()
    full_name = serializers.CharField(source='get_full_name', read_only=True)

    class Meta:
        model = User
        fields = ['id', 'email', 'firstname', 'lastname', 'full_name']

    def get_firstname(self, obj):
        return obj.firstname.title()
    
    def get_lastname(self, obj):
        return obj.lastname.title()

    
    def to_representation(self, instance):
        representation = super(UserSerializer, self).to_representation(instance)
        if instance.is_superuser:
            representation['admin'] = True
        return representation
    


class UserCreateSerializer(DjoserUserCreateSerializer):
    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ['id', 'username', 'email', 'password', 'first_name', 'last_name', 'address', 'phone_number']

    def validate_password(self, value):
        # First call the parent's validate_password method
        value = super().validate_password(value)
        
        # Then add Cognito-specific validations
        if not re.search(r'[A-Z]', value):
            raise serializers.ValidationError("Password must contain at least one uppercase letter.")
        
        if not re.search(r'[a-z]', value):
            raise serializers.ValidationError("Password must contain at least one lowercase letter.")
        
        if not re.search(r'[0-9]', value):
            raise serializers.ValidationError("Password must contain at least one number.")
        
        # Standard Cognito also requires special characters
        if not re.search(r'[^A-Za-z0-9]', value):
            raise serializers.ValidationError("Password must contain at least one special character.")
        
        # Cognito typically requires at least 8 characters
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters long.")
        
        return value
        
    def create(self, validated_data):
        """Create user in both Django DB and Cognito"""
        
        # First, create user with Djoser's standard method
        user = super().create(validated_data)
        
        
        return user
    

class UserRegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ('email', 'firstname', 'lastname', 'password', 'password_confirm')
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')
        
        if email and password:
            user = authenticate(email=email, password=password)
            if not user:
                raise serializers.ValidationError('Invalid credentials')
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled')
            attrs['user'] = user
            return attrs
        else:
            raise serializers.ValidationError('Must include email and password')


class SocialLoginSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    provider = serializers.ChoiceField(choices=['google', 'facebook'])



class CustomUserCreateSerializer(UserCreateSerializer):
    class Meta(UserCreateSerializer.Meta):
        model = User
        fields = ('id', 'email', 'firstname', 'lastname', 'password')

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class CustomUserSerializer(UserSerializer):
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta(UserSerializer.Meta):
        model = User
        fields = (
            'id', 'email', 'firstname', 'lastname', 'full_name',
            'profile_picture', 'date_joined', 'is_active'
        )
        read_only_fields = ('id', 'date_joined')