from rest_framework import serializers
from django.db import transaction
from .models import *
from main.models import *

# 협업 요청한/요청받은 가게 모음 리스트 response DTO
class CollaborationListSerializer(serializers.ModelSerializer):
    
    storeId = serializers.PrimaryKeyRelatedField(source='user', queryset=Profile.objects.all())
    
    
    class Meta:
        model = Collaborate
        
#

