from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
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
    
    
    try:
        with transaction.atomic():
            # User 생성 (패스워드 해싱)
            user = User.objects.create(
                username=username,
                password=make_password(password)  # 패스워드 해싱!
            )
            
            # Profile 생성
            profile = Profile.objects.create(
                User=user,
                profileName=name,
                profileNumber=phoneNumber
            )
            
            # JWT 토큰 생성
            refresh = RefreshToken.for_user(user)
            access_token = refresh.access_token
            
            return {
                "profile": profile,
                "tokens": {
                    "access": str(access_token),
                    "refresh": str(refresh)
                }
            }
            
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

def storeUpdate(storeId: int, user=None,type: int = None, category: int = None, 
                visitor: int = None, isWillingCollaborate: str = "", 
                storeContent: str = "", menus: list = None):
    
    try:
        store = get_object_or_404(Store, id=storeId)
        
        if store.user != user:
            raise DomainError("본인의 매장만 수정할 수 있습니다.")
        
        
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
        
        
        if menus is not None:
            # 기존 메뉴 삭제
            store.menus.all().delete()
            
            # 새 메뉴 추가
            for menu_data in menus:
                Menu.objects.create(
                    store=store,
                    name=menu_data['name'],
                    price=menu_data['price']
                )
        
        return store
        
    except Exception as e:
        raise DomainError(f"매장 업데이트 실패: {str(e)}")
