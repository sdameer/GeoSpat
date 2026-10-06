from django.db import models


class GeoSpatialFile(models.Model):
    file = models.FileField(upload_to="geospatial/")
    file_name = models.CharField(max_length=255, null=True, blank=True)
    crs = models.CharField(max_length=100)
    feature_count = models.IntegerField(null=True, blank=True)
    status = models.CharField(max_length=20, default="PROCESSING")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    
    
class GeoFeature(models.Model):
    file = models.ForeignKey(
        GeoSpatialFile,
        on_delete=models.CASCADE,
        related_name="features"
    )

    feature_index = models.IntegerField()
    geometry_type = models.CharField(max_length=50)
    geometry = models.JSONField()
    properties = models.JSONField()

    area = models.FloatField(null=True, blank=True)
    length = models.FloatField(null=True, blank=True)