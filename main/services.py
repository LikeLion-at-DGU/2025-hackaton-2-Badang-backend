from django.db import transaction
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from common.serializers import *
from main.models import *
from .models import *
from review.services import getStoreId, postReviewAnalysis
from django.contrib.auth import get_user_model
from django.db import transaction, IntegrityError
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class DomainError(Exception):
    def __init__(self, message, httpStatus=400):
        super().__init__(message)
        self.httpStatus = httpStatus
        
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


def storeCreate(name: str, address: str, user: Profile):
    res = getStoreId(name, address)
    if not res or not res.get("id"):
        raise DomainError("카카오 장소를 찾지 못했습니다.", httpStatus=400)

    kakaoId = res["id"]

    try:
        store, created = Store.objects.get_or_create(
            kakaoPlaceId=kakaoId,
            defaults={
                "user": user,
                "name": name,
                "address": address,
                "latitude": res.get("placeLatitude"),
                "longitude": res.get("placeLongitude"),
                "storeNumber": res.get("placePhone"),
            },
        )

        if not created:
            # 이미 존재하는 스토어
            if store.user_id != user.id:
                # 설계에 따라: 다른 유저가 선점한 경우 막기
                raise DomainError("이미 다른 사용자에 의해 등록된 매장입니다.", httpStatus=409)
            # 같은 유저가 다시 등록하면 업데이트만 하고 반환(원치 않으면 그냥 반환만 해도 됨)
            store.name = name
            store.address = address
            store.latitude = res.get("placeLatitude")
            store.longitude = res.get("placeLongitude")
            store.storeNumber = res.get("placePhone")
            store.save(update_fields=["name", "address", "latitude", "longitude", "storeNumber"])

        return store

    except IntegrityError:
        # 극단적인 동시성 케이스(두 요청이 동시에 들어온 경우 등)
        raise DomainError("이미 등록된 kakaoPlaceId 입니다.", httpStatus=409)

def storeUpdate(store: Store, **data) -> Store:
    """
    - 저장은 atomic 트랜잭션 안에서 끝낸다.
    - 무거운 후처리는 on_commit 으로 미룬다(응답 안정).
    - 메뉴/visitor 등 nested 입력을 방어적으로 처리.
    """
    # nested 입력 꺼내두기 (트랜잭션 밖에서 pop)
    visitorData = data.pop('visitor', None)
    menusData   = data.pop('menu', None)

    try:
        with transaction.atomic():
            # 1) visitor 처리 (dict 또는 id 모두 허용)
            if visitorData:
                if isinstance(visitorData, dict):
                    visitorObj, _ = Visitor.objects.get_or_create(**visitorData)
                else:
                    visitorObj = Visitor.objects.get(pk=visitorData)
                store.visitor = visitorObj

            # 2) FK/일반 필드 업데이트
            #   type, category가 id로 올 수도 있으니 둘 다 케이스 처리
            if 'type' in data and data.get('type') is not None:
                typeVal = data['type']
                store.type = Type.objects.get(pk=typeVal) if isinstance(typeVal, int) else typeVal

            if 'category' in data and data.get('category') is not None:
                categoryVal = data['category']
                store.category = Category.objects.get(pk=categoryVal) if isinstance(categoryVal, int) else categoryVal

            if 'isWillingCollaborate' in data and data.get('isWillingCollaborate') is not None:
                store.isWillingCollaborate = data['isWillingCollaborate']

            if 'storeContent' in data:
                store.content = data['storeContent']

            # 좌표/전화번호 등 다른 필드가 있으면 동일 패턴으로 추가
            # ex) if 'storeNumber' in data: store.storeNumber = data['storeNumber']

            store.full_clean()  # 모델 수준 검증(권장)
            store.save()

            # 3) 메뉴 갱신 (전부 교체하는 정책)
            if menusData is not None:
                store.menus.all().delete()
                bulk = []
                for m in menusData:
                    # 방어적 추출(키 누락 방지)
                    name = m.get('name')
                    price = m.get('price')
                    if not name:
                        raise ValidationError("메뉴 name은 필수입니다.")
                    bulk.append(Menu(store=store, name=name, price=price))
                if bulk:
                    Menu.objects.bulk_create(bulk)

            # 4) 무거운 후처리(외부 호출)는 커밋 후에 실행
            # def afterCommit():
            #     try:
            #         postReviewAnalysis(store.id, term=0)
            #         postReviewAnalysis(store.id, term=1)
            #     except Exception:
            #         logger.exception("postReviewAnalysis failed (store_id=%s)", store.id)
            #         # 실패해도 사용자 응답은 성공으로 유지

            # transaction.on_commit(afterCommit)

        return store

    except (ValidationError, IntegrityError) as e:
        # 비즈니스/무결성 문제는 DomainError로 승격해 400으로 내려가게
        raise DomainError(f"매장 정보 업데이트 오류: {str(e)}")
    except Exception as e:
        logger.exception("storeUpdate unexpected error (store_id=%s)", getattr(store, 'id', None))
        # 여기서 굳이 DomainError로 감싸면 400으로 내려가니, 진짜 서버오류면 상위에서 500 처리해도 됨
        raise