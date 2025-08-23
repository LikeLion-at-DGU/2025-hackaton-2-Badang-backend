from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.shortcuts import get_object_or_404, get_list_or_404
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from common.serializers import *
from main.models import *
from .models import *
from review.services import getStoreId, postReviewAnalysis

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
                user=user,
                profileName=name,
                profilePhoneNumber=phoneNumber
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

def storeCreate(name: str, address: str,user):
    
    try:
        
        profile = Profile.objects.get(user=user)
        res = getStoreId(name, address)
        
        store = Store.objects.create(
            user=profile,
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

def storeUpdate(store:Store, **data):
    
    try:
        # visitor 데이터가 딕셔너리 형태로 들어오면 처리
        if 'visitor' in data and data.get('visitor') is not None:
            visitor_data = data.pop('visitor')
            # visitor_data와 일치하는 객체를 찾거나, 없으면 새로 생성합니다.
            visitor_obj, created = Visitor.objects.get_or_create(**visitor_data)
            store.visitor = visitor_obj
    
            
        if 'type' in data and data.get('type') is not None:
            store.type = data['type']
        if 'category' in data and data.get('category') is not None:
            store.category = data['category']
        if 'isWillingCollaborate' in data and data.get('isWillingCollaborate') is not None:
            store.isWillingCollaborate = data['isWillingCollaborate']
        if 'storeContent' in data:
            store.content = data['storeContent']
            
        store.save()
        
        
        if 'menu' in data and data.get('menu') is not None:
            store.menus.all().delete()
            for menu_data in data['menu']:
                Menu.objects.create(store=store, **menu_data)
                
        postReviewAnalysis(store.id, term=0) # 전체 기간 리뷰 분석 데이터 생성
        postReviewAnalysis(store.id, term=1) # 한 달 리뷰 분석 데이터 생성
        
        return store
    
    except Exception as e:
        
        raise DomainError(f"매장 정보 업데이트 중 오류가 발생했습니다: {str(e)}")
