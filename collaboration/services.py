from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404, get_list_or_404
from common.serializers import *
from main.models import *
from .models import *

from rest_framework.permissions import AllowAny, IsAuthenticated
from django.core.exceptions import PermissionDenied

class DomainError(Exception):
    pass


@transaction.atomic
def createCollaboration(user, toStoreId: int, initialMessage: str = "") -> Collaborate:
    
    me = user.stores.first()
    
    if not me:
        # 소유한 가게가 없는 경우
        raise DomainError("소유한 가게 정보가 없습니다.")
    
    # 자기 가게에 신청 금지
    if toStoreId == me.id:
        raise DomainError("동일 가게 간 협업 신청은 불가합니다.")

    # 존재하는 가게인지 확인
    try:
        toStore = Store.objects.get(id=toStoreId)
    except Store.DoesNotExist:
        raise DomainError("유효하지 않은 가게 ID입니다.")
    
    # 중복 신청 방지
    dup = Collaborate.objects.filter(
    requestStore_id=me.id,
    responseStore_id=toStoreId,
    isAccepted__in=[Collaborate.Status.PENDING, Collaborate.Status.ACCEPTED]
).exists() | Collaborate.objects.filter(
    requestStore_id=toStoreId,
    responseStore_id=me.id,
    isAccepted__in=[Collaborate.Status.PENDING, Collaborate.Status.ACCEPTED]
).exists()
    if dup:
        raise DomainError("이미 대기 중인 요청이 있습니다.")

    collaboration = Collaborate.objects.create(
        requestStore_id=me.id,
        responseStore_id=toStoreId,
        initialMessage=initialMessage,
        requestMemo=initialMessage,
        responseMemo=initialMessage,
        isAccepted=Collaborate.Status.PENDING,
    )
    return collaboration

@transaction.atomic
def updateCollaborationMsg(collaborateId: int, user, memo: str = "") -> str:
    
    try:
        collab = Collaborate.objects.select_related('requestStore', 'responseStore').get(id=collaborateId)
    except Collaborate.DoesNotExist:
        raise DomainError("존재하지 않는 협업입니다.")

    if collab.requestStore.user != user and collab.responseStore.user != user:
        raise PermissionDenied("이 협업 정보를 수정할 권한이 없습니다.")
    
    # 요청자 메모 갱신 시도
    updated = (Collaborate.objects
               .filter(id=collaborateId, requestStore=user.stores.first())
               .update(requestMemo=memo))
    if updated:
        return memo

    # 응답자 메모 갱신 시도
    updated = (Collaborate.objects
               .filter(id=collaborateId, responseStore=user.stores.first())
               .update(responseMemo=memo))
    if updated:
        return memo

    # 여기까지 안 걸렸으면: 협업이 없거나, 해당 storeId가 소속 아님
    if Collaborate.objects.filter(id=collaborateId).exists():
        raise DomainError("해당 협업에 속한 가게가 아닙니다.")
    raise DomainError("유효하지 않은 협업 ID입니다.")


def deleteCollaboration(collaborateId: int, user) -> str:
    
    me = user.stores.first()
    
    if not Collaborate.objects.filter(id=collaborateId).exists():
        raise DomainError("유효하지 않은 협업 ID입니다.")
    
    if Collaborate.objects.filter(responseStore_id=me.id)| Collaborate.objects.filter(requestStore_id=me.id):
        delete = (Collaborate.objects
              .filter(id=collaborateId)
              .delete())
    
        if delete:
            return "삭제 완료"
    else:
        raise DomainError("협업 대상에 해당되지 않습니다.")
        
    
@transaction.atomic
def decisionCollaboration(collaborateId:int, isAccepted:str, user):
    
    me = user.stores.first()
    
    try:
        collab = Collaborate.objects.select_for_update().get(id=collaborateId)
    except Collaborate.DoesNotExist:
        raise DomainError("유효하지 않은 협업 ID입니다.")
    
    if collab.isAccepted != Collaborate.Status.PENDING:
        raise DomainError("이미 결정된 협업입니다.")
    
    if collab.responseStore.user != user:
        raise PermissionDenied("협업을 받은 가게가 아닙니다.")

    m = {"ACCEPTED": Collaborate.Status.ACCEPTED,
        "REJECTED": Collaborate.Status.REJECTED}

    try:
        new_status = m[isAccepted.upper()]
    except KeyError:
        raise DomainError("isAccepted 는 ACCEPTED/REJECTED만 허용합니다.")

    collab.isAccepted = new_status
    collab.save(update_fields=["isAccepted"])
    return "수락/거절 결정완료"