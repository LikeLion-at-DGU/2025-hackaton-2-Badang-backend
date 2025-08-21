from rest_framework.decorators import permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .models import *
from .serializers import *
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser

from .services import *
from .selectors import *


class DomainError(Exception):
    pass


class signupView(APIView):
    permission_classes= [AllowAny]
    
    def post(self, request):
        
        req = signupSerializer(data = request.data)
        req.is_valid(raise_exception=True)
        
        
        try:
            # 회원가입 처리
            result = profileCreate(
                username=req.validated_data["id"],
                password=req.validated_data["password"],
                name=req.validated_data["name"],
                phoneNumber=req.validated_data["phoneNumber"]
            )
            
            # 토큰을 쿠키에 설정 (settings의 JWT_AUTH_HTTPONLY=True와 맞춤)
            response = Response({
                'message': '회원가입 성공',
                'profileId': result['profile'].id,
            }, status=status.HTTP_201_CREATED)
            
            # HTTP-only 쿠키로 토큰 설정
            response.set_cookie(
                'access_token', 
                result['tokens']['access'],
                httponly=True,
                secure=True,  # HTTPS에서만
                samesite='Lax'
            )
            response.set_cookie(
                'refresh_token', 
                result['tokens']['refresh'],
                httponly=True,
                secure=True,
                samesite='Lax'
            )
            
            return response
            
        except DomainError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class storeView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        
        req = storeSerializerReq(data = request.data)
        req.is_valid(raise_exception=True)
        
        try:
            result = storeCreate(
                name=req.validated_data["name"],
                address=req.validated_data["address"],
                user=request.user 
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
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
    
    def patch(self, request):
        
        req = storeUpdateSerializerReq(data = request.data)
        req.is_valid(raise_exception=True)
        
        
        try:
            result = storeUpdate(
                storeId = req.validated_data["id"],
                user=request.user,
                type = req.validated_data["type"],
                category = req.validated_data["category"],
                visitor= req.validated_data["visitor"],
                isWillingCollaborate=req.validated_data["isWillingCollaborate"],
                storeContent= req.validated_data["storeContent"],
                menus=req.validated_data.get("menu", [])
            )
            
            return Response({
                "message": "상세정보 등록 완료",
                "statusCode": "200",
                "data": {
                    "id": result.id,
                    "name": result.name
                }
            }, status=status.HTTP_200_OK)
            
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class loginView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        req = loginSerializer(data=request.data)
        req.is_valid(raise_exception=True)
        
        try:
            # 1. Service를 호출하여 유저 인증 및 기본 정보, 토큰을 받습니다.
            result = profileLogin(
                username=req.validated_data["id"],
                password=req.validated_data["password"]
            )
            
            # 2. 인증된 user 객체를 사용하여 연결된 storeId를 찾습니다.
            store_id = None
            try:
                # 2-1. User 객체로 Profile 객체를 찾습니다. (필드명: userId)
                profile = Profile.objects.get(userId=result['user'])
                
                # 2-2. Profile 객체로 Store 객체를 찾습니다. (필드명: user)
                #      만약 Store 모델의 필드명이 다르다면 이 부분도 수정해야 합니다.
                store = Store.objects.get(user=profile) 
                store_id = store.id
            except (Profile.DoesNotExist, Store.DoesNotExist):
                # 해당 유저에게 연결된 프로필이나 가게가 없어도 오류 없이 진행합니다.
                # store_id는 그대로 None 값을 유지합니다.
                pass
            
            # 3. 최종 응답 데이터를 구성합니다.
            response_data = {
                'message': '로그인 성공',
                'userId': result['user'].id,
                'username': result['user'].username,
                'storeId': store_id  # 위에서 찾은 store_id를 포함합니다.
            }
            
            response = Response(response_data, status=status.HTTP_200_OK)
            
            # 4. HTTP-only 쿠키로 토큰을 설정합니다.
            response.set_cookie(
                'access_token', 
                result['tokens']['access'],
                httponly=True,
                secure=False,  # 개발 환경에서는 False, 배포 시에는 True로 변경
                samesite='Lax'
            )
            response.set_cookie(
                'refresh_token', 
                result['tokens']['refresh'],
                httponly=True,
                secure=False,  # 개발 환경에서는 False, 배포 시에는 True로 변경
                samesite='Lax'
            )
            
            return response
            
        except DomainError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


class logoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            
            if not refresh_token:
                return Response({
                    'error': 'refresh token이 없습니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 로그아웃 처리
            profileLogout(refresh_token)
            
            response = Response({
                'message': '로그아웃 성공'
            }, status=status.HTTP_200_OK)
            
            # 쿠키에서 토큰 제거
            response.delete_cookie('access_token')
            response.delete_cookie('refresh_token')
            
            return response
            
        except DomainError as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


# 추가: 토큰 갱신 기능 (선택사항)
class tokenRefreshView(APIView):
    permission_classes = [AllowAny]
    
    def post(self, request):
        try:
            refresh_token = request.COOKIES.get('refresh_token')
            
            if not refresh_token:
                return Response({
                    'error': 'refresh token이 없습니다.'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 새로운 access token 생성
            token = RefreshToken(refresh_token)
            new_access_token = token.access_token
            
            response = Response({
                'message': '토큰 갱신 성공'
            }, status=status.HTTP_200_OK)
            
            # 새 access token을 쿠키에 설정
            response.set_cookie(
                'access_token',
                str(new_access_token),
                httponly=True,
                secure=False,
                samesite='Lax'
            )
            
            return response
            
        except Exception as e:
            return Response({
                'error': '토큰 갱신 실패'
            }, status=status.HTTP_400_BAD_REQUEST)