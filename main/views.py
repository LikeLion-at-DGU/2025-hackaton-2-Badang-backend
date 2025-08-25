from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import PermissionDenied, ValidationError # DRF 예외 사용
from django.conf import settings
from django.utils import timezone
import logging

from .services import *
from .selectors import *
from review.services import postReviewAnalysis

logger = logging.getLogger(__name__)
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

GENDER_DISPLAY_TO_CODE = {"남": "M", "여": "F", "기타": "O"}
AGE_DISPLAY_TO_CODE    = {"청소년": 0, "청년": 1, "중년": 2, "노년": 3}

class signupView(APIView):
    permission_classes= [AllowAny]
    authentication_classes = []
    
    def post(self, request):
        req = signupSerializer(data = request.data)
        req.is_valid(raise_exception=True)
        
        try:
            result = profileCreate(
                username=req.validated_data["username"],
                password=req.validated_data["password"],
                name=req.validated_data["name"],
                phoneNumber=req.validated_data["phoneNumber"]
            )
            
            body = {
                "message": "회원가입 성공",
                "profileId": result["profile"].user_id,          
                "username": result["profile"].profileName,       
                "id": result["profile"].user.username            
            }

            response = Response(body, status=status.HTTP_201_CREATED)
            
            # secure=True로 일관성 유지 (HTTPS 환경에서만 쿠키 전송)
            response.set_cookie(
                'access_token', 
                result['tokens']['access'],
                httponly=True,
                secure=True,
                samesite='None'
            )
            response.set_cookie(
                'refresh_token', 
                result['tokens']['refresh'],
                httponly=True,
                secure=True,
                samesite='None'
            )

            return response
            
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            # 예상 밖 서버 오류 -> 500
            if getattr(settings, 'DEBUG', False):
                # 개발 환경에서는 상세 트레이스 반환 (간편 디버깅용)
                import traceback
                tb = traceback.format_exc()
                return Response({"error": "서버 오류가 발생했습니다.", "trace": tb}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            return Response({"error": "서버 오류가 발생했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def normalizeStoreDict(dataDict: dict) -> dict:
    if not isinstance(dataDict, dict):
        return dataDict

    # visitor 변환
    visitor = dataDict.get("visitor")
    normVisitor = None
    if visitor:
        genderDisplay = visitor.get("gender")        
        ageDisplay    = visitor.get("ageGroup")        
        isForeign     = visitor.get("isForeign")

        normVisitor = {
            
            "gender": GENDER_DISPLAY_TO_CODE.get(genderDisplay, None),
            
            "ageGroup": AGE_DISPLAY_TO_CODE.get(ageDisplay, None),
            
            "isForeign": bool(isForeign) if isForeign is not None else None,
        }

    menu = dataDict.get("menu") or []

    return {
        "id": dataDict.get("id"),
        "name": dataDict.get("name"),
        "address": dataDict.get("address"),
        "visitor": normVisitor,
        "menu": menu,
        "type": dataDict.get("type"),
        "category": dataDict.get("category"),
        "isWillingCollaborate": dataDict.get("isWillingCollaborate"),
        "storeContent": dataDict.get("storeContent"),
    }


class storeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        
        user = request.user.profile
        req = storeSerializerReq(data = request.data)
        req.is_valid(raise_exception=True)
        
        try:
            # request.user가 Profile 객체라고 가정합니다.
            result = storeCreate(
                name=req.validated_data["name"],
                address=req.validated_data["address"],
                user= user
            )
            
            return Response({
                "message": "가게 정보 등록 완료",
                "statusCode": "201",
                "data": {
                    "id": result.id,
                    "name": result.name,
                    "address": result.address
                }
            }, status=status.HTTP_201_CREATED)
            
            
            
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def patch(self, request):
        
        store = request.user.profile.stores.first()
        
        # 가게가 존재하지 않는 경우 (예: 아직 가게를 등록하지 않은 사용자)
        if not store:
            return Response({"detail": "수정할 가게를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)

        # 시리얼라이저는 이제 id 없이 데이터만 검증합니다.
        req = storeUpdateSerializerReq(data=request.data)
        req.is_valid(raise_exception=True)
        
        try:
            # 검증된 store 객체와 데이터를 서비스 함수에 전달합니다.
            resultDict = storeUpdate(store=store, **req.validated_data)
            normalized = normalizeStoreDict(resultDict)
            
            if not resultDict.get("menu"):
                store.refresh_from_db()
                resultDict["menu"] = [
                    {"name": m.name, "price": m.price}
                    for m in store.menus.all()
                ]

            
            return Response({
                "message": "상세정보 등록 완료",
                "statusCode": "200",
                "data": normalized,
            }, status=200)
            
            
        
        except DomainError as e:
            logger.info("storeUpdate domain error: %s", e)
            return Response({"error": str(e)}, status=400)
        except IntegrityError as e:
            logger.exception("storeUpdate integrity error")
            return Response({"error": "데이터 무결성 오류(중복/제약 충돌)입니다."}, status=400)
        except Exception as e:
            logger.exception("storeUpdate unexpected error")
            return Response({"error": "서버 오류가 발생했습니다."}, status=500)


class loginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        req = loginSerializer(data=request.data)
        req.is_valid(raise_exception=True)

        try:
            result = profileLogin(
                username=req.validated_data["id"],
                password=req.validated_data["password"]
            )
            # result 예시: {"user": <User>, "profile": <Profile>, "tokens": {...}}

            # 프로필(혹은 프로필에 연결된 스토어) 기준으로 조회
            profile = result["user"].profile
            stores_qs = Store.objects.filter(user=profile)

            stores = storeReadSerializer(stores_qs, many=True).data

            # 리뷰 분석 로직 (백그라운드에서 실행)
            first_store = stores_qs.first()
            if first_store:
                print(f"[LOGIN] Store found: {first_store.id}, name: {first_store.name}")
                logger.info(f"Login successful for user with store: {first_store.id}, name: {first_store.name}")
                
                # 리뷰 분석 데이터 확인 및 생성
                try:
                    from review.models import ReviewAnalysis
                    
                    # 기존 분석 데이터 조회 (올바른 방법)
                    existing_analyses = ReviewAnalysis.objects.filter(storeId=first_store)
                    print(f"[LOGIN] Existing analyses count: {existing_analyses.count()}")
                    logger.info(f"Existing analyses count: {existing_analyses.count()}")
                    
                    should_create_analysis = False
                    
                    if existing_analyses.count() == 0:
                        print("[LOGIN] No existing analyses found. Will create new ones...")
                        logger.info("No existing analyses found. Will create new ones...")
                        should_create_analysis = True
                    else:
                        # 최신 분석의 업데이트 날짜 확인
                        latest_analysis = existing_analyses.order_by('-updatedAt').first()
                        if latest_analysis:
                            days_since_update = (timezone.now() - latest_analysis.updatedAt).days
                            print(f"[LOGIN] Latest analysis updated {days_since_update} days ago")
                            logger.info(f"Latest analysis updated {days_since_update} days ago")
                            
                            if days_since_update > 3:
                                print("[LOGIN] Analysis is older than 3 days. Will create new ones...")
                                logger.info("Analysis is older than 3 days. Will create new ones...")
                                should_create_analysis = True
                            else:
                                print("[LOGIN] Analysis is recent. No need to update.")
                                logger.info("Analysis is recent. No need to update.")
                    
                    # 리뷰 분석 생성 (백그라운드에서)
                    if should_create_analysis:
                        import threading
                        def create_analysis():
                            try:
                                print("[LOGIN] Starting background review analysis...")
                                logger.info("Starting background review analysis...")
                                postReviewAnalysis(first_store.id, term=0)
                                postReviewAnalysis(first_store.id, term=1)
                                print("[LOGIN] Background review analysis completed successfully")
                                logger.info("Background review analysis completed successfully")
                            except Exception as e:
                                print(f"[LOGIN] Background review analysis failed: {e}")
                                logger.error(f"Background review analysis failed: {e}")
                        
                        # 백그라운드 스레드에서 실행
                        thread = threading.Thread(target=create_analysis)
                        thread.daemon = True
                        thread.start()
                        print("[LOGIN] Background analysis thread started")
                        logger.info("Background analysis thread started")
                
                except Exception as e:
                    print(f"[LOGIN] Error in review analysis logic: {e}")
                    logger.error(f"Error in review analysis logic: {e}")
                    # 분석 실패해도 로그인은 정상 진행
            else:
                print("[LOGIN] User has no stores")
                logger.info("Login successful for user with no stores")

            response = Response({
                "message": "로그인 성공",
                "stores": stores
            }, status=status.HTTP_200_OK)

            # 쿠키 설정 (개발 중 http라면 secure=False 가능, 배포는 꼭 True+None)
            response.set_cookie(
                "access_token",
                result["tokens"]["access"],
                httponly=True,
                secure=True,
                samesite='None'  # 크로스사이트라면 "None"
            )
            response.set_cookie(
                "refresh_token",
                result["tokens"]["refresh"],
                httponly=True,
                secure=True,
                samesite='None'  # 크로스사이트라면 "None"
            )
            return response

        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class logoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        # 발급 시 실제 사용했던 값들로 최종 통일할 예정이지만,
        # 지금은 마이그레이션용으로 "싹쓸이 삭제"를 한다.
        candidateDomains = [None, "doyoun.shop", ".doyoun.shop"]
        candidatePaths = ["/", "/api", "/backend"]  # 프로젝트에 맞게 추가/수정
        cookieSameSite = "None"
        cookieSecure = True

        refreshToken = request.COOKIES.get("refresh_token")
        if refreshToken:
            try:
                profileLogout(refreshToken)
            except DomainError as e:
                resp = Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                self.nukeCookies(resp, candidateDomains, candidatePaths, cookieSameSite, cookieSecure)
                return resp

        resp = Response({"message": "로그아웃 성공"}, status=status.HTTP_200_OK)
        self.nukeCookies(resp, candidateDomains, candidatePaths, cookieSameSite, cookieSecure)

        # 캐시 무효화(혹시모를 CDN/브라우저 캐시 방지)
        resp["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        resp["Pragma"] = "no-cache"
        return resp

    def nukeCookies(self, resp, domains, paths, samesite, secure):
        for name in ["access_token", "refresh_token"]:
            # 1) delete_cookie 모든 조합
            for d in domains:
                for p in paths:
                    resp.delete_cookie(name, domain=d, path=p, samesite=samesite)
            # 2) 만료값으로 덮어쓰기(혹시 모를 브라우저 이슈용)
            for d in domains:
                for p in paths:
                    resp.set_cookie(
                        name, "", max_age=0, expires=0,
                        domain=d, path=p,
                        secure=secure, httponly=True, samesite=samesite
                    )



class tokenRefreshView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        refresh_token = request.COOKIES.get('refresh_token')
        if not refresh_token:
            return Response({'error': 'refresh token이 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            token = RefreshToken(refresh_token)
            new_access_token = str(token.access_token)
            
            response = Response({'message': '토큰 갱신 성공'}, status=status.HTTP_200_OK)
            
            # secure=True로 통일하여 보안 강화
            response.set_cookie(
                'access_token',
                new_access_token,
                httponly=True,
                secure=True,
                samesite='None'
            )
            
            return response
            
        except Exception as e:
            return Response({'error': '유효하지 않은 토큰입니다.'}, status=status.HTTP_401_UNAUTHORIZED)

class meView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        profile = request.user.profile
        stores = Store.objects.filter(user=profile)
        return Response({
            "id": request.user.username,
            "profileId": profile.user_id,
            "username": profile.profileName,
            "stores": storeReadSerializer(stores, many=True).data
        }, status=status.HTTP_200_OK)