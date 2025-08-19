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
    
#협업 가능 가게 찾기
class CollaborationSearchReq(serializers.Serializer):
    type = serializers.IntegerField(required=False)
    category = serializers.IntegerField(required=False)
    query = serializers.CharField(required=False, allow_blank=True, default="")
    storeId = serializers.IntegerField()
    
class CollaborationSearchRes(serializers.Serializer):
    store = StoreBrief()
    
    def to_representation(self, store):
        return {"store": {
            "storeId": store.id, 
            "name": store.name,
            "latitude": store.latitude,
            "longitude": store.longitude,
            "address": store.address,
        }}

# 협업 신청시 필요한 DTO
class CollaborationCreateReq(serializers.Serializer):
    fromStoreId = serializers.IntegerField()
    toStoreId = serializers.IntegerField()
    initialMessage = serializers.CharField(allow_blank=True, required=False, default="")

class CollaborationCreatedResp(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    isAccepted = serializers.ChoiceField(choices=["PENDING"])
    
    
    
#수락 거절 DTO
class CollaborationDecisionReq(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    isAccepted = serializers.ChoiceField(choices=["ACCEPTED","REJECTED"])

class CollaborationDecisionResp(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    isAccepted = serializers.ChoiceField(choices=["ACCEPTED","REJECTED"])
  
    
    
#협업 요청받은 건 관련 DTO
class IncomingItem(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    requestStore = StoreBrief()
    initialMemo = serializers.CharField(allow_blank=True)
    
    def to_representation(self, obj: Collaborate):
        partner = obj.requestStore

        return {
            "collaborateId": obj.id,
            "resquestStore": {
                "storeId": partner.id,
                "storeName": partner.name,
                "storeLatitude": partner.latitude,
                "storeLongitude": partner.longitude,
                "address": partner.address,
            },
            # 처음 신청 메시지
            "initialMemo": obj.initialMessage or "",
        }




#협업 요청한 건 관련 DTO
class OutgoingItem(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    responseStore = StoreBrief()
    initialMemo = serializers.CharField(allow_blank=True)
    
    def to_representation(self, obj: Collaborate):
        partner = obj.responseStore

        return {
            "collaborateId": obj.id,
            "responseStore": {
                "storeId": partner.id,
                "storeName": partner.name,
                "storeLatitude": partner.latitude,
                "storeLongitude": partner.longitude,
                "address": partner.address,
            },
            # 처음 신청 메시지
            "initialMemo": obj.initialMessage or "",
        }



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
    collaborateId = serializers.IntegerField()
    storeId = serializers.IntegerField()
    memo = serializers.CharField(allow_blank=True)
    


#협업 끝난 가게 삭제
class CollaborationDeleteResp(serializers.Serializer):
    deletedCollaborateId = serializers.IntegerField()

