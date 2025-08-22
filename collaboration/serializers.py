from rest_framework import serializers
from django.db import transaction

from .models import *
from main.models import *
from common.serializers import *
from .services import *
from .selectors import *


# ---------------------------
# 공용: 가게 요약 DTO
# ---------------------------
class StoreBrief(serializers.ModelSerializer):
    storeId = serializers.IntegerField(source="id", read_only=True)
    number = serializers.CharField(source="user.profilePhoneNumber", read_only=True)
    # 외래키 id만 내려주고 싶으면 *_id 소스로 매핑
    type = serializers.IntegerField(source="type_id", read_only=True)
    category = serializers.IntegerField(source="category_id", read_only=True)

    class Meta:
        model = Store
        fields = (
            "storeId",
            "name",
            "number",
            "latitude",
            "longitude",
            "address",
            "type",
            "category",
            "isWillingCollaborate",
        )
        read_only_fields = fields


# ---------------------------
# 협업 가능 가게 검색
# ---------------------------
class CollaborationSearchReq(serializers.Serializer):
    type = serializers.IntegerField(required=False)
    category = serializers.IntegerField(required=False)
    query = serializers.CharField(required=False, allow_blank=True, default="")


class CollaborationSearchRes(serializers.Serializer):
    store = StoreBrief(read_only=True)

    # 리스트/단건 공용으로 쓰기 쉽게 store 인스턴스를 그대로 받도록
    def to_representation(self, store: Store):
        return {"store": StoreBrief(store).data}


# ---------------------------
# 협업 생성
# ---------------------------
class CollaborationCreateReq(serializers.Serializer):
    toStoreId = serializers.IntegerField()
    initialMessage = serializers.CharField(allow_blank=True, required=False, default="")


class CollaborationCreatedResp(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    # 항상 PENDING으로만 응답하려면 Choice보다는 CharField + default/read_only가 명확
    isAccepted = serializers.CharField(default="PENDING")


# ---------------------------
# 협업 수락/거절
# ---------------------------
class CollaborationDecisionReq(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    isAccepted = serializers.ChoiceField(choices=["ACCEPTED", "REJECTED"])


class CollaborationDecisionResp(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    isAccepted = serializers.ChoiceField(choices=["ACCEPTED", "REJECTED"])


# ---------------------------
# 수신함(내가 받은 협업 요청)
# ---------------------------
class IncomingItem(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    requestStore = StoreBrief()
    initialMemo = serializers.CharField(allow_blank=True)

    def to_representation(self, obj: Collaborate):
        return {
            "collaborateId": obj.id,
            "requestStore": StoreBrief(obj.requestStore).data,
            "initialMemo": obj.initialMessage or "",
        }


# ---------------------------
# 보낸함(내가 보낸 협업 요청)
# ---------------------------
class OutgoingItem(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    responseStore = StoreBrief()
    initialMemo = serializers.CharField(allow_blank=True)

    def to_representation(self, obj: Collaborate):
        return {
            "collaborateId": obj.id,
            "responseStore": StoreBrief(obj.responseStore).data,
            "initialMemo": obj.initialMessage or "",
        }


# ---------------------------
# 진행 중인 협업 항목
# ---------------------------
class ActiveItem(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    collaborateStore = StoreBrief()
    memo = serializers.CharField(allow_blank=True)
    startedAt = serializers.DateTimeField()

    def to_representation(self, obj: Collaborate):
        myStoreId = self.context.get("storeId")

        # 내가 요청자면 파트너=응답자, 내 메모는 requestMemo (반대의 경우 responseMemo)
        if obj.requestStore_id == myStoreId:
            partner = obj.responseStore
            memo = obj.requestMemo or ""
        else:
            partner = obj.requestStore
            memo = obj.responseMemo or ""

        # 모델에 createdAt만 있다면 startedAt으로 이름만 바꿔 내려줌
        started = getattr(obj, "createdAt", None) or getattr(obj, "startedAt", None)

        return {
            "collaborateId": obj.id,
            "collaborateStore": StoreBrief(partner).data,
            "memo": memo,
            "startedAt": started,
        }


# ---------------------------
# 협업 메모 수정
# ---------------------------
class CollaborationMemoPatchReq(serializers.Serializer):
    collaborateId = serializers.IntegerField()
    memo = serializers.CharField(allow_blank=True)


# ---------------------------
# 협업 삭제 응답
# ---------------------------
class CollaborationDeleteResp(serializers.Serializer):
    deletedCollaborateId = serializers.IntegerField()
