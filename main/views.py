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
        