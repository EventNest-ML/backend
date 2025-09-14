from django.db import models
from django.utils.translation import gettext_lazy as _


# from django.contrib.postgres.fields import ArrayField, JSONField
# import uuid



# class Polygon(models.Model):
#     map = models.ForeignKey('Map', on_delete=models.CASCADE, related_name='polygons')
#     name = models.CharField(max_length=100)
#     description = models.TextField(null=True, blank=True)
#     image_path = models.CharField(max_length=200, null=True, blank=True)
#     polygon_metadata = JSONField(null=True, blank=True)
#     coordinates = ArrayField(models.FloatField(), null=True, blank=True)
#     # geom = models.PolygonField(srid=26331)  # Removed GIS field
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)

#     approval_orders = models.ManyToManyField(
#         'ApprovalOrder',
#         through='PolygonApprovalOrderAssociation',
#         related_name='polygons'
#     )


# class Map(models.Model):
#     name = models.CharField(max_length=500, unique=True, null=True, blank=True)
#     district = models.CharField(max_length=500, null=True, blank=True)
#     coordinates_str = models.CharField(max_length=500, null=True, blank=True)
#     utm_str = models.CharField(max_length=500, null=True, blank=True)
#     # center_coordinates = models.PointField(srid=4326, null=True, blank=True)  # Removed GIS field
#     # utm_coordinates = models.PointField(srid=32631, null=True, blank=True)  # Removed GIS field
#     bearing = models.FloatField(null=True, blank=True)
#     image_path = models.CharField(max_length=255, null=True, blank=True, unique=True)
#     image_hash = models.CharField(max_length=64, null=True, blank=True, unique=True)
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)



# class GoogleMapsBasemapOutline(models.Model):
#     district_name = models.CharField(max_length=500)
#     coordinates = JSONField()
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)



# class PolygonApprovalDetails(models.Model):
#     polygon = models.ForeignKey(
#         'Polygon',
#         on_delete=models.CASCADE,
#         related_name='approval_details'
#     )
#     polygon_name = models.CharField(max_length=100, null=True, blank=True)
#     coordinates = ArrayField(models.FloatField(), null=True, blank=True)
#     geom_string = models.TextField(null=True, blank=True)
#     # wkb_geometry = models.PolygonField(srid=26331, null=True, blank=True)  # Removed GIS field
#     junction_id = models.IntegerField(null=True, blank=True)
#     approval_order = models.ForeignKey(
#         'ApprovalOrder',
#         on_delete=models.CASCADE,
#         related_name='polygon_details'
#     )
#     country = models.CharField(max_length=100, null=True, blank=True)
#     state = models.CharField(max_length=100, null=True, blank=True)
#     district = models.CharField(max_length=100, null=True, blank=True)
#     zone = models.CharField(max_length=100, null=True, blank=True)
#     subzone = models.CharField(max_length=100, null=True, blank=True)
#     approved_uses = models.TextField(null=True, blank=True)
#     street_location = ArrayField(models.CharField(max_length=100), null=True, blank=True)
#     block_plot_boundary = models.TextField(null=True, blank=True)
#     min_floor = models.IntegerField(null=True, blank=True)
#     max_floor = models.IntegerField(null=True, blank=True)
#     max_height = models.IntegerField(null=True, blank=True)
#     units_per_hectare = models.CharField(max_length=50, null=True, blank=True)
#     setbacks = JSONField(null=True, blank=True)
#     soft_landscape_percentage = models.FloatField(null=True, blank=True)
#     building_coverage_percentage = models.FloatField(null=True, blank=True)
#     parking_requirement = models.TextField(null=True, blank=True)
#     permissible_uses = ArrayField(models.CharField(max_length=100), null=True, blank=True)
#     remarks = models.TextField(null=True, blank=True)
#     approval_order_created_at = models.DateTimeField(null=True, blank=True)
#     approval_order_updated_at = models.DateTimeField(null=True, blank=True)
#     json_data = JSONField(null=True, blank=True)

#     class Meta:
#         db_table = 'polygon_approval_details'
#         unique_together = ('polygon', 'junction_id')

# class DistrictInfo(models.Model):
#     menu_name = models.CharField(max_length=255)
#     db_name = models.CharField(max_length=255)
#     default_coordinates_lat = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
#     default_coordinates_lng = models.DecimalField(max_digits=10, decimal_places=6, null=True, blank=True)
#     offset_northing = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
#     offset_easting = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)


# # Note: ApprovalOrder model is referenced but not defined in the provided code.
# # Here's a basic version that would work with the relationships:
# class ApprovalOrder(models.Model):
#     id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
#     # Add other fields as needed
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)