from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404, get_list_or_404
from common.serializers import *
from main.models import *
from .models import *

class DomainError(Exception):
    pass


@transaction.atomic
def createCollaboration(fromStoreId: int, toStoreId: int, initialMessage: str = "") -> Collaborate:
    # 자기 가게에 신청 금지
    if fromStoreId == toStoreId:
        raise DomainError("동일 가게 간 협업 신청은 불가합니다.")

    # 존재하는 가게인지 확인
    if not Store.objects.filter(id=fromStoreId).exists() or not Store.objects.filter(id=toStoreId).exists():
        raise DomainError("유효하지 않은 가게 ID입니다.")

    # 중복 신청 방지
    dup = Collaborate.objects.filter(
    requestStore_id=fromStoreId,
    responseStore_id=toStoreId,
    isAccepted__in=[Collaborate.Status.PENDING, Collaborate.Status.ACCEPTED]
).exists() | Collaborate.objects.filter(
    requestStore_id=toStoreId,
    responseStore_id=fromStoreId,
    isAccepted__in=[Collaborate.Status.PENDING, Collaborate.Status.ACCEPTED]
).exists()
    if dup:
        raise DomainError("이미 대기 중인 요청이 있습니다.")

    collaboration = Collaborate.objects.create(
        requestStoreId=fromStoreId,
        responseStoreId=toStoreId,
        initialMessage=initialMessage,
        requestMemo=initialMessage,
        responseMemo=initialMessage,
        isAccepted=Collaborate.Status.PENDING,
    )
    return collaboration

@transaction.atomic
def updateCollaborationMsg(collaborateId: int, storeId: int, memo: str = "") -> str:
    # 요청자 메모 갱신 시도
    updated = (Collaborate.objects
               .filter(id=collaborateId, requestStore_id=storeId)
               .update(requestMemo=memo))
    if updated:
        return memo

    # 응답자 메모 갱신 시도
    updated = (Collaborate.objects
               .filter(id=collaborateId, responseStore_id=storeId)
               .update(responseMemo=memo))
    if updated:
        return memo

    # 여기까지 안 걸렸으면: 협업이 없거나, 해당 storeId가 소속 아님
    if Collaborate.objects.filter(id=collaborateId).exists():
        raise DomainError("해당 협업에 속한 가게가 아닙니다.")
    raise DomainError("유효하지 않은 협업 ID입니다.")