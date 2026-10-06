from django.contrib import admin
from app_geo.models import GeoSpatialFile, GeoFeature

admin.site.register(GeoSpatialFile)
admin.site.register(GeoFeature)
