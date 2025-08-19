from rest_framework import serializers
from django.db import transaction
from .models import *
from review.services import getStoreId


class ProfileSerializer(serializers.ModelSerializer):
    id = serializers.CharField(write_only=True)              # -> User.username
    password = serializers.CharField(write_only=True, min_length=4)
    name = serializers.CharField(source='profileName')
    phoneNumber = serializers.CharField(source='profilePhoneNumber')
    
    userId = serializers.IntegerField(source='pk', read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'password', 'name', 'phoneNumber', 'userId']
        read_only_fields = [
            'userId'
        ]

    @transaction.atomic
    def create(self, validated_data):
        username = validated_data.pop('id')
        raw_pw = validated_data.pop('password')
        user = User(username=username)
        user.set_password(raw_pw)
        user.save()
        profile = Profile.objects.create(userId=user, **validated_data)
        return profile



#---response 전용 serializer--

class MenuReadSerializer(serializers.ModelSerializer):
    class Meta:
        model = Menu
        fields = ['id', 'name', 'price']


#가게 설정 후 선택 정보 넘어가기 전 받을 response(가게 id) 
class StoreRegisterResponseSerializer(serializers.ModelSerializer):
    id, phoneNumber, placeLatitude, placeLongitude = getStoreId(storeName=Store.name, storeAddress=Store.address)  # 카카오맵 API 활용. 카카오맵
    
    class Meta:
        model = Store
        fields = [
            'id','name'
        ]
        
#가게 상세 정보 설정 후 받을 response
class StoreDetailRegisterResponseSerializer(serializers.ModelSerializer):
    menus = MenuReadSerializer(many=True, read_only=True)
    
    class Meta:
        model = Store
        fields ='__all__'



#---request 전용 serializer --

#가게 설정 시 request
class StoreRegisterRequestSerializer(serializers.ModelSerializer):
    
    userId = serializers.PrimaryKeyRelatedField(source='user', queryset=Profile.objects.all())
    
    class Meta:
        model = Store
        fields = [
            'userId','name', 'address'
        ]
        
        
#menu 이름, 가격으로 입력받기
class MenuSerializer(serializers.Serializer):
    name = serializers.CharField(max_length=50)
    price = serializers.IntegerField(min_value=0)

    # 필요하면 여기서 추가 검증 가능
    def validate_name(self, v):
        v = v.strip()
        if not v:
            raise serializers.ValidationError("메뉴 이름이 비어 있습니다.")
        return v
    
#가게 상세 정보 요청 requset
class StoreDetailRegisterRequestSerializer(serializers.ModelSerializer):
    isWillingCollaborate = serializers.BooleanField(source='is_willing_collaborate', required=False)
    storeContent = serializers.CharField(source='content', required=False, allow_blank=True)
    #선택 항목들
    type = serializers.PrimaryKeyRelatedField(queryset=Type.objects.all(), required=True, allow_null=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=True, allow_null=True)
    visitor = serializers.PrimaryKeyRelatedField(queryset=Visitor.objects.all(), required=True, allow_null=True)
    
    #직접 입력하시는 메뉴
    menus = MenuSerializer(many=True, required=False)
     
    class Meta:
        model = Store
        fields = [
            'type',
            'category',
            'visitor',
            'isWillingCollaborate',
            'storeContent',
            'menus',
        ]
    @transaction.atomic
    def update(self, instance: Store, validated_data):
        menus = validated_data.pop('menus', None)

        # 기본 필드 적용
        for k, v in validated_data.items():
            setattr(instance, k, v)
        instance.save()

        if menus is not None:
            instance.menus.all().delete()
            to_create = [Menu(store=instance, name=m['name'], price=m['price']) for m in menus]
            if to_create:
                Menu.objects.bulk_create(to_create)

        return instance