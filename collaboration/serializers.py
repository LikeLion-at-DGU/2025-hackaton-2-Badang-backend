from rest_framework import serializers
from django.db import transaction
from .models import *
from main.models import *
from common.serializers import *
from .services import *
from .selectors import *

#store 정보 관련 묶음
class StoreBrief(serializers.Serializer):
    storeId = serializers.IntegerField()
    name = serializers.CharField()
    latitude = serializers.FloatField()
    longitude = serializers.FloatField()
    address = serializers.CharField()
    


# 협업 신청시 필요한 DTO
class CollaborationCreateReq(serializers.Serializer):
    fromStoreId = serializers.IntegerField()
    toStoreId = serializers.IntegerField()
    initialMessage = serializers.CharField(allow_blank=True, required=False, default="")

class CollaborationCreatedResp(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    IsAccepted = serializers.ChoiceField(choices=["PENDING"])
    
    
    
#수락 거절 DTO
class CollaborationDecisionReq(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    IsAccepted = serializers.ChoiceField(choices=["ACCEPT","REJECT"])

class CollaborationDecisionResp(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    IsAccepted = serializers.ChoiceField(choices=["ACCEPTED","REJECTED"])
  
    
    
#협업 요청받은 건 관련 DTO
class IncomingListReq(serializers.Serializer):
    responseStoreId = serializers.IntegerField(required=False)  # 필요 시
    page = serializers.IntegerField(min_value=1, default=1)
    size = serializers.IntegerField(min_value=1, max_value=100, default=20)

class IncomingItem(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    requestStore = StoreBrief()
    initialMessage = serializers.CharField(allow_blank=True)
    IsAccepted = serializers.ChoiceField(choices=["PENDING","CANCELLED"])  # 설계에 맞게
    requestedAt = serializers.DateTimeField()

class IncomingListResp(serializers.Serializer):
    items = IncomingItem(many=True)
    total = serializers.IntegerField()



#협업 요청한 건 관련 DTO
class OutgoingListReq(serializers.Serializer):
    requestStoreId = serializers.IntegerField(required=False)
    page = serializers.IntegerField(min_value=1, default=1)
    size = serializers.IntegerField(min_value=1, max_value=100, default=20)

class OutgoingItem(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    responseStore = StoreBrief()
    IsAccepted = serializers.ChoiceField(choices=["PENDING","ACCEPTED","REJECTED"])
    initialMessage = serializers.CharField(allow_blank=True)
    updatedAt = serializers.DateTimeField()



#협업 중인 건 관련 DTO
class ActiveListReq(serializers.Serializer):
    storeId = serializers.IntegerField(required=False)
    
    
class ActiveItem(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    collaborateStore = StoreBrief()
    memo = serializers.CharField(allow_blank=True)
    startedAt = serializers.DateTimeField()
    
    def to_representation(self, obj: Collaborate):
        my_store_id = self.context.get("storeId")

        # 내가 요청자면 파트너=응답자, 메모는 내가 적은 requestMemo(반대도 동일)
        if obj.requestStore_id == my_store_id:
            partner = obj.responseStore
            memo = obj.requestMemo or ""
        else:
            partner = obj.requestStore
            memo = obj.responseMemo or ""

        return {
            "collaborateId": obj.id,
            "collaborateStore": {
                "storeId": partner.id,
                "name": partner.name,
                "latitude": partner.latitude,
                "longitude": partner.longitude,
                "address": partner.address,
            },
            "memo": memo,
            "createdAt": obj.createdAt,
        }



#협업 메모 수정
class CollaborationMemoPatchReq(serializers.Serializer):
    memo = serializers.CharField(allow_blank=True)
    
class CollaborationMemoPatchResp(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    memo = serializers.CharField()
    updatedAt = serializers.DateTimeField()


#협업 끝난 가게 삭제
class CollaborationDeleteResp(serializers.Serializer):
    deleted = serializers.BooleanField()
