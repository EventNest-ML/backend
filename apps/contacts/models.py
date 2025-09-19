from django.db import models
from django.contrib.auth import get_user_model

# Create your models here.


User = get_user_model()


class Contact(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name="contacts")
    name = models.CharField(max_length=255)
    email = models.EmailField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("owner", "email")  # Prevent duplicate contact emails per owner
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.name} <{self.email}>"
