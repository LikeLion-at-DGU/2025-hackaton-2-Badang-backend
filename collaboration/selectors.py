from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404, get_list_or_404

from common.serializers import *
from main.models import *
from .models import *

#가게 정보 반환 (재사용)
def store_detail_dict(store) -> dict:
    return {
        "storeId": store.id,
        "name": store.name,
        "latitude": store.latitude,
        "longitude": store.longitude,
        "address": store.address,
    }

#협업중인 가게 목록 반환
def getActiveCollaboration(storeId : int):
    
    req_qs = (Collaborate.objects
              .filter(requestStore_id=storeId, isAccepted=Collaborate.Status.ACCEPTED)
              .select_related("requestStore", "responseStore"))

    res_qs = (Collaborate.objects
              .filter(responseStore_id=storeId, isAccepted=Collaborate.Status.ACCEPTED)
              .select_related("requestStore", "responseStore"))

    rows = list(req_qs) + list(res_qs)
    # 최신순 정렬
    rows.sort(key=lambda c: c.createdAt, reverse=True)
    return rows