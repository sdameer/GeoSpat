from django.urls import path
from app_geo.views import *

urlpatterns = [
    path("files/",AddGeoSpatialData.as_view()),
    path("files/<int:id>",GetGeoSpatialData.as_view()),
    # path("files/<int:id>/measurements/",AddGeoSpatialData.as_view()),
]