from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth.hashers import make_password
from common.serializers import *
from main.models import *
from .models import *
from review.services import getStoreId, postReviewAnalysis
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError

class DomainError(Exception):
    pass

@transaction.atomic
def profileCreate(username: str = "", password: str = "", name: str = "", phoneNumber: str = ""):
    User = get_user_model()

    # (선택) 입력 정리
    username = (username or "").strip()
    if not username or not password:
        raise DomainError("아이디와 비밀번호는 필수입니다.")

    try:
        # 1) User 생성 (create_user가 비밀번호 해싱까지 처리)
        user = User.objects.create_user(username=username, password=password)
    except IntegrityError:
        # username unique 충돌(경쟁 상황 포함)
        raise DomainError("이미 사용 중인 아이디입니다.")

    
    profile = Profile.objects.create(
        user=user,
        profileName=name,
        profilePhoneNumber=phoneNumber
    )

    
    refresh = RefreshToken.for_user(user)
    accessToken = str(refresh.access_token)
    refreshToken = str(refresh)

    
    return {
        "profile": profile,
        "tokens": {
            "access": accessToken,
            "refresh": refreshToken
        }
    }

def storeCreate(name: str, address: str,user:Profile):
    
    try:
        
        res = getStoreId(name, address)
        
        store = Store.objects.create(
            user=user,
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
