from django.contrib import admin
from .models import Event, Collaborator, Invitation

# Register your models here.
admin.site.register(Event)
admin.site.register(Collaborator)
class InvitationAdmin(admin.ModelAdmin):
    list_display=['event', 'sent_by','token', 'email', 'expires_at', 'status']
admin.site.register(Invitation, InvitationAdmin)