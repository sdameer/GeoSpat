import os
import json
from django.db import transaction

import geopandas as gpd
from rest_framework import serializers
from app_geo.models import GeoSpatialFile , GeoFeature

from shapely.geometry import mapping


class AddGeoSpatialDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoSpatialFile
        fields = "__all__"
        read_only_fields = [
            "file_name",
            "crs",
            "feature_count",
            "status",
        ]
        
    def validate_file(self, file):
        """
           only the zip and kml files are accepted for this api     
        """        
        if not file.name.lower().endswith((".zip", ".kml")):
            raise serializers.ValidationError(
                "Only .zip and .kml files are supported."
            )

        return file     


    @transaction.atomic
    # atomicity : either complete hte whole process 
    # or cancel the whole process
    def create(self, validated_data):
        uploaded_file = validated_data["file"]

        obj = GeoSpatialFile.objects.create(
            file=uploaded_file,
            file_name=uploaded_file.name,
            status="PROCESSING",
        )

        try:
            # read the incoming uploaded file
            gdf = gpd.read_file(obj.file.path)

            if gdf.empty:
                raise serializers.ValidationError(
                    "The uploaded file contains no features."
                )

            if gdf.crs is None:
                raise serializers.ValidationError(
                    "The uploaded file does not contain CRS information."
                )

            # Store file-level information
            obj.crs = str(gdf.crs)
            obj.feature_count = len(gdf)

            # Process every feature
            for index, row in gdf.iterrows():

                geometry = row.geometry
                geometry_type = geometry.geom_type

                # Convert properties into JSON-safe data
                properties = json.loads(
                    gdf.iloc[[index]].drop(columns="geometry").to_json(orient="records")
                )[0]

                area = None
                length = None

                # Calculate measurement only for supported geometries
                if geometry_type in ["Polygon", "MultiPolygon", "LineString"]:

                    feature_gdf = gpd.GeoDataFrame(
                        {"geometry": [geometry]},
                        crs=gdf.crs
                    )

                    # Convert geographic CRS to projected CRS
                    if feature_gdf.crs.is_geographic:
                        projected_crs = feature_gdf.estimate_utm_crs()

                        if projected_crs:
                            feature_gdf = feature_gdf.to_crs(projected_crs)

                    projected_geometry = feature_gdf.geometry.iloc[0]

                    if geometry_type in ["Polygon", "MultiPolygon"]:
                        area = projected_geometry.area

                    elif geometry_type == "LineString":
                        length = projected_geometry.length

                # Store the feature
                GeoFeature.objects.create(
                    file=obj,
                    feature_index=int(index),
                    geometry_type=geometry_type,
                    geometry=mapping(geometry),
                    properties=properties,
                    area=area,
                    length=length,
                )

            obj.status = "COMPLETED"
            obj.save()

            return obj

        except Exception:
            obj.status = "FAILED"
            obj.save()
            raise    
        
        
        
        
class GetGeoSpatialDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = GeoSpatialFile
        exclude = ["file","uploaded_at"]
        
        
class GetGeoSpatialDataSerializerMeasurements(serializers.ModelSerializer):
    class Meta :
        model = GeoSpatialFile
        