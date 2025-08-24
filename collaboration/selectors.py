from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404, get_list_or_404
from django.core.exceptions import PermissionDenied
from rest_framework.response import Response

from common.serializers import *
from main.models import *
from .models import *
import math
from .services import DomainError
from typing import Optional


# 가까운 거리 정렬 위한 계산용
def _haversine_km(lat1, lon1, lat2, lon2) -> float:
    
    #위도 경도 안잡히면
    if None in (lat1, lon1, lat2, lon2):
        raise ValueError("haversine: 위도 경도 좌표가 제대로 입력되지 않았습니다")
    
    R = 6371.0  # 지구 반지름(km)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R * c


#협업중인 가게 목록 반환
def getActiveCollaboration(user):
    
    me = user.stores.first()
    
    req_qs = (Collaborate.objects
              .filter(requestStore_id=me.id, isAccepted=Collaborate.Status.ACCEPTED)
              .select_related("requestStore", "responseStore"))

    res_qs = (Collaborate.objects
              .filter(responseStore_id=me.id, isAccepted=Collaborate.Status.ACCEPTED)
              .select_related("requestStore", "responseStore"))

    rows = list(req_qs) + list(res_qs)
    # 최신순 정렬
    rows.sort(key=lambda c: c.createdAt, reverse=True)
    
    return rows

# 내가 협업을 '요청한' 목록 (요청자 = 나), 보통 대기중만
def getRequestCollaboration(user):
    
    me = user.stores.first()
    
    qs = (
        Collaborate.objects
        .filter(requestStore_id=me.id, isAccepted=Collaborate.Status.PENDING) 
        .select_related("requestStore", "responseStore")                           
        .order_by("-createdAt")                                                   
    )
    return list(qs)

# 내가 협업을 '요청받은' 목록 (응답자 = 나), 보통 대기중만
def getResponseCollaboration(user):
    
    me = user.stores.first()
    
    qs = (
        Collaborate.objects
        .filter(responseStore_id=me.id, isAccepted=Collaborate.Status.PENDING)  
        .select_related("requestStore", "responseStore")                           
        .order_by("-createdAt")                                                   
    )
    return list(qs)

#협업 가능한 가게 8개 반환
def getCollaborationSearch(user,
                        typeId: Optional[int] = None,
                        categoryId: Optional[int] = None,
                        query: str = ""):
    distanceKm = _haversine_km  # 기존 함수 래퍼

    me = user.stores.first()
    if not me:
        raise DomainError("소유한 가게 정보가 없습니다.")
    if me.latitude is None or me.longitude is None:
        raise DomainError("내 가게의 위치 정보가 없습니다.")

    # 1) 필터 조건만 적용 (자기 자신 제외 + 협업 가능 + 좌표 존재)
    baseQs = (
        Store.objects
        .filter(isWillingCollaborate=True, latitude__isnull=False, longitude__isnull=False)
        .exclude(id=me.id)
    )
    if typeId is not None:
        baseQs = baseQs.filter(type=typeId)
    if categoryId is not None:
        baseQs = baseQs.filter(category=categoryId)
    if query:
        baseQs = baseQs.filter(name__icontains=query)

    # 2) 거리 계산 후 정렬
    candidates = []
    for s in baseQs:
        d = distanceKm(me.latitude, me.longitude, s.latitude, s.longitude)
        candidates.append((d, s))
    candidates.sort(key=lambda x: x[0])

    # 3) 제외 목록 (이미 협업 중/요청/응답)
    activeIds = [c.requestStore_id for c in getActiveCollaboration(user)] + \
                [c.responseStore_id for c in getActiveCollaboration(user)]
    requestIds = [c.responseStore_id for c in getRequestCollaboration(user)]
    responseIds = [c.requestStore_id for c in getResponseCollaboration(user)]
    excludeIds = set(activeIds + requestIds + responseIds)

    # 4) 거리순으로 훑으면서 제외대상 스킵, 최대 8개 채우기
    picked = []
    for _, store in candidates:
        if store.id in excludeIds:
            continue
        picked.append(store)
        if len(picked) == 9:
            break

    return picked