from rest_framework import serializers
from .models import *


#---response 전용 serializer--

#가게 설정 후 선택 정보 넘어가기 전 받을 response(가게 id) 
class StoreResgisterResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            'id','name'
        ]
        
#가게 상세 정보 설정 후 받을 response
class StoreDetailRegisterResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            '__all__'
        ]



#---request 전용 serializer --

#가게 설정 시 request
class StoreRegisterRequestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Store
        fields = [
            'name', 'address'
        ]
        
        
#menu 이름, 가격으로 입력받기
class MenuItemWriteSerializer(serializers.Serializer):
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
    
    #선택 항목들
    type = serializers.PrimaryKeyRelatedField(queryset=Type.objects.all(), required=True, allow_null=True)
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all(), required=True, allow_null=True)
    visitor = serializers.PrimaryKeyRelatedField(queryset=Visitor.objects.all(), required=True, allow_null=True)
    
    #직접 입력하시는 메뉴
    menus = MenuItemWriteSerializer(many=True, required=False)
     
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
        extra_kwargs = {
            'content': {'required': False}, 
            'is_willing_collaborate': {'required': False}
        }
        