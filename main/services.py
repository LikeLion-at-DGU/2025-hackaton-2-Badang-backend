from django.db import transaction
from django.utils import timezone
from django.shortcuts import get_object_or_404, get_list_or_404
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from common.serializers import *
from main.models import *
from .models import *
from review.services import getStoreId

class DomainError(Exception):
    pass

def profileCreate(username: str = "", password: str = "", name: str = "", phoneNumber: str = ""):
    """
    JWT 방식 회원가입
    - User 생성 시 패스워드 해싱
    - 트랜잭션 처리로 안전성 보장
    """
    try:
        with transaction.atomic():
            # User 생성 (패스워드 해싱)
            user = User.objects.create(
                username=username,
                password=make_password(password) 
            )
            
            # Profile 생성
            profile = Profile.objects.create(
                User=user,
                profileName=name,
                profileNumber=phoneNumber
            )
            
            return profile
            
    except Exception as e:
        raise DomainError(f"회원가입 실패: {str(e)}")

def storeCreate(name: str = "", address: str = ""):
    
    try:
        res = getStoreId(name, address)
        
        store = Store.objects.create(
            name=name,
            address=address,
            kakaoPlaceId=res.get("id"),
            latitude=res.get("placeLatitude"),
            longitude=res.get("placeLongitude"),
            storeNumber=res.get("placePhone")
        )
        
        return store
        
    except Exception as e:
        raise DomainError(f"매장 생성 실패: {str(e)}")

def storeUpdate(store_id: int, type: int = None, category: int = None, 
                visitor: int = None, isWillingCollaborate: str = "", 
                storeContent: str = ""):
    
    try:
        store = get_object_or_404(Store, id=store_id)
        
        # None이 아닌 값들만 업데이트
        if type is not None:
            store.type = type
        if category is not None:
            store.category = category
        if visitor is not None:
            store.visitor = visitor
        if isWillingCollaborate:
            store.isWillingCollaborate = isWillingCollaborate
        if storeContent:
            store.storeContent = storeContent
            
        store.save()
        return store
        
    except Exception as e:
        raise DomainError(f"매장 업데이트 실패: {str(e)}")
