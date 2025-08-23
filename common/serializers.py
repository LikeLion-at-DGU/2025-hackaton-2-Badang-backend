from rest_framework import serializers
from .models import *

class CommonResponseSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=255)
    status = serializers.IntegerField(default=400)
    
    if status == 400:
        error = serializers.CharField(default="BadRequest")

    if status == 401:
        error = serializers.CharField(default="Unauthorized")

    if status == 403:
        error = serializers.CharField(default="Forbidden")
        
    if status == 404:
        error = serializers.CharField(default="NotFound")
        
    if status == 500:
        error = serializers.CharField(default="InternalServerError")