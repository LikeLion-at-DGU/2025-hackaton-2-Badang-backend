from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404, get_list_or_404

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

# #가게 정보 반환 (재사용)
# def store_detail_dict(store) -> dict:
#     return {
#         "storeId": store.id,
#         "name": store.name,
#         "latitude": store.latitude,
#         "longitude": store.longitude,
#         "address": store.address,
#     }

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

# 내가 협업을 '요청한' 목록 (요청자 = 나), 보통 대기중만
def getRequestCollaboration(storeId: int):
    qs = (
        Collaborate.objects
        .filter(requestStore_id=storeId, isAccepted=Collaborate.Status.PENDING)   # ✅ 요청자=나
        .select_related("requestStore", "responseStore")                           # ✅ N+1 방지
        .order_by("-createdAt")                                                   # ✅ DB 정렬
    )
    return list(qs)

# 내가 협업을 '요청받은' 목록 (응답자 = 나), 보통 대기중만
def getResponseCollaboration(storeId: int):
    qs = (
        Collaborate.objects
        .filter(responseStore_id=storeId, isAccepted=Collaborate.Status.PENDING)  # ✅ 응답자=나
        .select_related("requestStore", "responseStore")                           # ✅ 타이포 수정 + N+1 방지
        .order_by("-createdAt")                                                   # ✅ DB 정렬
    )
    return list(qs)

def getCollaborationSearch(storeId:int, 
                            type_: Optional[int] = None,
                            category_: Optional[int] = None,
                            query:str=""):
    
    try:
        me = Store.objects.only("latitude", "longitude").get(id=storeId)
    except Store.DoesNotExist:
        raise DomainError("유효하지 않은 가게 ID입니다.")
    
    # 후보 골라내기 (자기 자신 제외 + 협업 가능만)
    qs = (Store.objects
        .filter(isWillingCollaborate=True)
        .exclude(id=storeId))
    
    if type_ is not None:
        qs = qs.filter(type=type_)
    if category_ is not None:
        qs = qs.filter(category=category_)
        
    #query 가 이름에 포함된 가게로 필터링
    if query:
        qs = qs.filter(name__icontains=query)

    candidates = []
    for s in qs:
        d = _haversine_km(me.latitude, me.longitude, s.latitude, s.longitude)
        candidates.append((d, s))

    candidates.sort(key=lambda x: x[0])
    # Top 8만 반환
    top = candidates[:8]
    
    return [s for _, s in top]