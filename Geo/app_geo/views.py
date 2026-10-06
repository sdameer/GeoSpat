from rest_framework.views import APIView , Response
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser

from app_geo.serializers import (
    AddGeoSpatialDataSerializer , 
    GetGeoSpatialDataSerializer,
    GetGeoSpatialDataSerializerMeasurements,
    )
from app_geo.models import GeoSpatialFile , GeoFeature

class AddGeoSpatialData(APIView):
    """
        This API accepts the file 
        and returns the json as per required 
        format with the geospatial information 
        extracted from the file        
    """
    
    parser_classes = [MultiPartParser , FormParser]
    
    def post(self , request):
        print(request.content_type)
        print("DATA:", request.data)
        print("FILES:", request.FILES)
        serializer = AddGeoSpatialDataSerializer(data = request.data)
        if serializer.is_valid():
            obj = serializer.save()
            response_json = {
                    "id": obj.id, # type: ignore
                    "filename": obj.file_name, # type: ignore
                    "feature_count": obj.feature_count, # type: ignore
                    "crs": obj.crs, # type: ignore
                    "status": obj.status, # type: ignore
                },

            return Response(response_json,
                status=status.HTTP_201_CREATED
            )
            return Response(serializer.data , status=status.HTTP_201_CREATED)
        return Response(serializer.errors , status=status.HTTP_400_BAD_REQUEST)


class GetGeoSpatialData(APIView):
    def get(self ,request , id):
        obj = GeoSpatialFile.objects.get(id = id)
        serializer = GetGeoSpatialDataSerializer(obj)        
        return Response(serializer.data ,status=status.HTTP_200_OK)
    
class GetGeoSpatialDataMeasurements(APIView):
    def get(self ,request , id):
        obj = GeoSpatialFile.objects.get(id = id)
        serializer = GetGeoSpatialDataSerializerMeasurements(obj)        
        return Response(serializer.data ,status=status.HTTP_200_OK)    