from django.db import transaction
from django.utils import timezone

from common.serializers import *
from main.models import *
from .models import *

class DomainError(Exception):
    pass


@transaction.atomic
def createCollaboration(from_store_id: int, to_store_id: int, initial_message: str = "") -> Collaborate:
    if from_store_id == to_store_id:
        raise DomainError("동일 가게 간 협업 신청은 불가합니다.")

    # 존재하는 가게인지 확인
    if not Store.objects.filter(id=from_store_id).exists() or not Store.objects.filter(id=to_store_id).exists():
        raise DomainError("유효하지 않은 가게 ID입니다.")

    # 중복 PENDING 방지
    dup = Collaborate.objects.filter(
        requestStore_id=from_store_id,
        responseStore_id=to_store_id,
        isAccepted=Collaborate.Status.PENDING
    ).exists()
    if dup:
        raise DomainError("이미 대기 중인 요청이 있습니다.")

    collab = Collaborate.objects.create(
        requestStore_id=from_store_id,
        responseStore_id=to_store_id,
        initialMessage=initial_message,
        requestMemo=initial_message,
        responseMemo=initial_message,
        isAccepted=Collaborate.Status.PENDING,
    )
    return collab