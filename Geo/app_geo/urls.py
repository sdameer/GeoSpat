from django.urls import path
from app_geo.views import *

urlpatterns = [
    path("",first.as_view())
]