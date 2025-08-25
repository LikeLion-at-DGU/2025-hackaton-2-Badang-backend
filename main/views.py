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

from .services import *
from .selectors import *
from review.services import postReviewAnalysis

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
            
            # 또는 최소 필드만
            # stores = list(stores_qs.values("id", "name", "address"))

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
        cookieDomain = ".doyoun.shop"
        cookiePath = "/"
        cookieSameSite = "None"
        cookieSecure = True

        refreshToken = request.COOKIES.get("refresh_token")

        if refreshToken:
            try:
                profileLogout(refreshToken)
            except DomainError as e:
                resp = Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
                # 1) host-only 쿠키 삭제 (domain 생략)
                resp.delete_cookie("access_token", path=cookiePath, samesite=cookieSameSite)
                resp.delete_cookie("refresh_token", path=cookiePath, samesite=cookieSameSite)
                # 2) .doyoun.shop 쿠키 삭제
                resp.delete_cookie("access_token", path=cookiePath, domain=cookieDomain, samesite=cookieSameSite)
                resp.delete_cookie("refresh_token", path=cookiePath, domain=cookieDomain, samesite=cookieSameSite)
                return resp

        resp = Response({"message": "로그아웃 성공"}, status=status.HTTP_200_OK)

        # 1) host-only 먼저
        resp.delete_cookie("access_token", path=cookiePath, samesite=cookieSameSite)
        resp.delete_cookie("refresh_token", path=cookiePath, samesite=cookieSameSite)
        # 2) .doyoun.shop 도 같이
        resp.delete_cookie("access_token", path=cookiePath, domain=cookieDomain, samesite=cookieSameSite)
        resp.delete_cookie("refresh_token", path=cookiePath, domain=cookieDomain, samesite=cookieSameSite)

        # (선택) 만료 덮어쓰기
        for name in ["access_token", "refresh_token"]:
            resp.set_cookie(name, "", max_age=0, expires=0,
                            path=cookiePath, secure=cookieSecure, httponly=True, samesite=cookieSameSite)
            resp.set_cookie(name, "", max_age=0, expires=0,
                            path=cookiePath, domain=cookieDomain, secure=cookieSecure, httponly=True, samesite=cookieSameSite)
        return resp


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