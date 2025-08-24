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
from django.utils import timezone



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
            result = storeUpdate(store=store, **req.validated_data)
            
            # storeId = result.id
            # postReviewAnalysis(storeId=storeId, term=0)
            # postReviewAnalysis(storeId=storeId, term=1)
            
            return Response({
                "message": "상세정보 등록 완료",
                "statusCode": "200",
                "data": storeReadSerializer(result).data,
            }, status=status.HTTP_200_OK)
            
            
        
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)



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
            
            # 가게에 연결된 리뷰 분석 데이터가 없거나 마지막 업데이트 후 3일 경과시 postReviewAnalysis 호출

            first_store = stores_qs.first()
            if first_store:
                review_analyses = getattr(first_store, 'review_analysis', None)
                if review_analyses is not None:
                    if review_analyses.count() == 0:
                        postReviewAnalysis(first_store.id, term=0)
                        postReviewAnalysis(first_store.id, term=1)
                    else:
                        latest_analysis = review_analyses.order_by('-updatedAt').first()
                        if latest_analysis and (timezone.now() - latest_analysis.updatedAt).days > 3:
                            postReviewAnalysis(first_store.id, term=0)
                            postReviewAnalysis(first_store.id, term=1)

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
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            if not refresh_token:
                return Response({'error': 'refresh token이 없습니다.'}, status=status.HTTP_400_BAD_REQUEST)
            
            profileLogout(refresh_token)
            
            response = Response({'message': '로그아웃 성공'}, status=status.HTTP_200_OK)
            
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            
            return response
            
        except DomainError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


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
        menu = Menu.objects.filter(store__in=stores)
        return Response({
            "id": request.user.username,
            "profileId": profile.user_id,
            "username": profile.profileName,
            "stores": storeReadSerializer(stores, many=True).data,
            "menu": MenuSerializer(menu, many=True).data
        }, status=status.HTTP_200_OK)