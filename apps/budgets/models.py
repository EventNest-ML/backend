from django.db import models
# from django.contrib.postgres.fields import ArrayField, JSONField
# import uuid
# from enum import Enum

# Enum for ApprovalPDF status
# class StatusEnum(Enum):
#     PENDING = "PENDING"
#     EXTRACTED = "EXTRACTED"
#     FAILED = "FAILED"

# class ApprovalOrder(models.Model):
#     id = models.UUIDField(
#         primary_key=True,
#         default=uuid.uuid4,
#         editable=False
#     )
#     zone = models.CharField(max_length=100, null=True, blank=True)
#     subzone = models.CharField(max_length=100, null=True, blank=True)
#     street_location = ArrayField(
#         models.CharField(max_length=256),
#         default=list,
#         null=True,
#         blank=True
#     )
#     block_plot_boundary = ArrayField(
#         models.CharField(max_length=256),
#         default=list,
#         null=True,
#         blank=True
#     )
#     min_floor = models.FloatField(null=True, blank=True)
#     max_floor = models.FloatField(null=True, blank=True)
#     max_height = models.FloatField(null=True, blank=True)
#     units_per_hectare = models.CharField(max_length=50, null=True, blank=True)
#     setbacks = JSONField(null=True, blank=True)
#     soft_landscape_percentage = models.FloatField(null=True, blank=True)
#     building_coverage_percentage = models.FloatField(null=True, blank=True)
#     parking_requirement = models.TextField(null=True, blank=True)
#     permissible_uses = ArrayField(
#         models.CharField(max_length=256),
#         default=list,
#         null=True,
#         blank=True
#     )
#     remarks = models.TextField(null=True, blank=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = 'approval_order'

#     def __str__(self):
#         return f"<ApprovalOrder: {self.zone} - {self.subzone} />"

# class ApprovalPDF(models.Model):
#     STATUS_CHOICES = [
#         (StatusEnum.PENDING.value, 'Pending'),
#         (StatusEnum.EXTRACTED.value, 'Extracted'),
#         (StatusEnum.FAILED.value, 'Failed'),
#     ]

#     id = models.UUIDField(
#         primary_key=True,
#         default=uuid.uuid4,
#         editable=False
#     )
#     name = models.CharField(max_length=255, null=True, blank=True)
#     file_path = models.CharField(max_length=255, null=True, blank=True)
#     file_hash = models.CharField(max_length=64)
#     country = models.CharField(max_length=100, default="NG", null=True, blank=True)
#     state = models.CharField(max_length=100, null=True, blank=True)
#     district = models.CharField(max_length=100, null=True, blank=True)
#     extraction_status = models.CharField(
#         max_length=20,
#         choices=STATUS_CHOICES,
#         default=StatusEnum.PENDING.value
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = 'approval_order_pdf'

#     def __str__(self):
#         return f"<PDF - ID: {self.id}/>"

# class ApprovalOrderPDFLink(models.Model):
#     id = models.UUIDField(
#         primary_key=True,
#         default=uuid.uuid4,
#         editable=False
#     )
#     approval_order = models.ForeignKey(
#         'ApprovalOrder',
#         on_delete=models.CASCADE,
#         related_name='approval_orders'
#     )
#     approval_pdf = models.ForeignKey(
#         'ApprovalPDF',
#         on_delete=models.CASCADE,
#         related_name='pdf_file'
#     )
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     class Meta:
#         db_table = 'approval_order_pdf_link'

#     def __str__(self):
#         return f"<Link: {self.approval_order} -> {self.approval_pdf} />"