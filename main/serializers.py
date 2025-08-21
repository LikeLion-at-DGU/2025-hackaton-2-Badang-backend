from rest_framework import serializers
from django.db import transaction
from .models import *
from review.services import getStoreId



class signupSerializer(serializers.Serializer):
    id = serializers.CharField()
    password = serializers.CharField()
    name = serializers.CharField()
    phoneNumber = serializers.CharField()
    
class storeSerializerReq(serializers.Serializer):
    name = serializers.CharField()
    address = serializers.CharField()
    
    
class MenuSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    price = serializers.IntegerField(min_value=0)

    # 필요하면 여기서 추가 검증 가능
    def validate_name(self, v):
        v = v.strip()
        if not v:
            raise serializers.ValidationError("메뉴 이름이 비어 있습니다.")
        return v
    
    
class storeUpdateSerializerReq(serializers.Serializer):
    type = serializers.IntegerField()
    category = serializers.IntegerField()
    visitor = serializers.IntegerField()
    isWillingCollaborate = serializers.CharField()
    storeContent = serializers.CharField(required=False, allow_blank=True, default="")
    menu = MenuSerializer(many=True, required=False)
    
    