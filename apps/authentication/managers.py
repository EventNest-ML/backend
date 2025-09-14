from django.contrib.auth.models import BaseUserManager
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.utils.translation import gettext_lazy as _
import logging


logger = logging.getLogger(__name__)



class CustomUserManager(BaseUserManager):

    def email_validator(self, email):
        try:
            validate_email(email)
        except ValidationError:
            raise ValueError(_("You must provide a valid email address"))

    def create_user(self, firstname, lastname, email, password=None, **extra_fields):
        if not firstname:
            raise ValueError(_("Users must submit a first name"))
        if not lastname:
            raise ValueError(_("Users must submit a last name"))
        if email:
            email = self.normalize_email(email)
            self.email_validator(email)
        else:
            raise ValueError(_("Base User Account: An email address is required"))
        
        user = self.model(
            firstname=firstname,
            lastname=lastname,
            email=email,
            **extra_fields
        )

        # # Save user locally in Django
        user.set_password(password)
        user.save(using=self._db)
        print(f"User {email} saved in Django database.")
        return user
    
    def create_superuser(self, firstname, lastname, email, password, **extra_fields):

        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError(_("Superusers must have is_staff=True"))

        if extra_fields.get('is_superuser') is not True:
            raise ValueError(_("Superusers must have is_superuser=True"))

        if not password:
            raise ValueError(_("Superusers must have a password"))
        
        if email:
            email = self.normalize_email(email)
            self.email_validator(email)
        else:
            raise ValueError(_("Admin Account: An email address is required"))

        user = self.create_user(firstname, lastname, email, password, **extra_fields)
        user.save(using=self._db)
        return user

    
