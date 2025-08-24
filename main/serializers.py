from rest_framework import serializers
from django.db import transaction
from .models import *
from rest_framework.validators import UniqueValidator
from django.contrib.auth import get_user_model



class signupSerializer(serializers.Serializer):
    # 프론트 키(id)를 그대로 받되, 내부 키는 username으로 매핑
    id = serializers.CharField(max_length=150, source='username')
    password = serializers.CharField(write_only=True)
    name = serializers.CharField(max_length=50)
    phoneNumber = serializers.CharField(max_length=15)

    def validate_username(self, value):
        UserModel = get_user_model()
        normalized = (value or "").strip().lower()
        if not normalized:
            raise serializers.ValidationError("아이디는 필수입니다.")
        # 케이스 무시 중복 체크
        if UserModel.objects.filter(username__iexact=normalized).exists():
            raise serializers.ValidationError("이미 사용 중인 아이디입니다.")
        return normalized  # 정규화된 username을 서비스로 넘김
    
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
    
    class Meta:
        fields = ['name', 'price']
    
    
class VisitorSerializer(serializers.ModelSerializer):
    class Meta:
        model = Visitor
        fields = ['gender', 'age_group', 'is_foreign']

class storeUpdateSerializerReq(serializers.Serializer):

    type = serializers.PrimaryKeyRelatedField(queryset=Type.objects.all(), required=False)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=False)
    visitor = VisitorSerializer(required=False)
    isWillingCollaborate = serializers.BooleanField(required=False)
    storeContent = serializers.CharField(required=False, allow_blank=True)
    menu = MenuSerializer(many=True, required=False)

class loginSerializer(serializers.Serializer):
    id = serializers.CharField()
    password = serializers.CharField(write_only=True) 
    
class storeReadSerializer(serializers.ModelSerializer):
    ownerName = serializers.CharField(source='user.profileName', read_only=True) 
    
    class Meta:
        model = Store
        fields = "__all__"
