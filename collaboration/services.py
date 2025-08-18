from django.db import transaction
from django.utils import timezone

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