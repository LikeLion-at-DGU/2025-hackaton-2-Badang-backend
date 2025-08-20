from django.shortcuts import render
from rest_framework import viewsets, mixins
from django.db import transaction
from .models import *
from .serializers import *
from rest_framework.views import APIView

from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from rest_framework import status

import re

from .permissions import IsOwnerReadOnly
from rest_framework.decorators import action


# Create your views here.

# responseDto 반환 형태
def ok(data, message="성공", code=status.HTTP_200_OK):
    return Response({"message": message, "statusCode": code, "data": data}, status=code)

def bad(message="잘못된 요청", code=status.HTTP_400_BAD_REQUEST, errors=None):
    return Response({"message": message, "statusCode": code, "data": errors or []}, status=code)


class ProfileViewSet(viewsets.ModelViewSet):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer

    
    # 테스트 기간: 전부 오픈하려면
    permission_classes = [AllowAny]          # ✅ 리스트(또는 튜플)로, 클래스 자체를 넣는다

    # (나중에 잠글 때)
    # def get_permissions(self):
    #     if self.action == "create":        # 회원가입만 오픈
    #         return [AllowAny()]
    #     return [IsAuthenticated()]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        profile = serializer.save()  # create()에서 User+Profile 동시 생성
        return ok({"userId": profile.pk}, message="프로필등록완료", code=status.HTTP_201_CREATED)



class StoreViewSet(viewsets.ModelViewSet):
    
    queryset = Store.objects.all().select_related('user', 'type', 'category', 'visitor').prefetch_related('menus')

    def get_serializer_class(self):
        if self.action == 'create':
            return StoreRegisterRequestSerializer            
        if self.action in ['partial_update', 'update']:
            return StoreDetailRegisterRequestSerializer      
        
        #post,patch 아니면 응답용
        return StoreDetailRegisterResponseSerializer      


    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        store = serializer.save() 
        
        return ok({"id": store.id, "name": store.name}, message="가게 등록 완료", code=status.HTTP_201_CREATED)

    
    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance=instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        store = serializer.save()  
        response = StoreDetailRegisterResponseSerializer(store)
        return ok(response.data, message="정보 등록완료", code=status.HTTP_200_OK)
    
class LoginView(APIView):
    # 완전 오픈
    permission_classes = [AllowAny]
    authentication_classes = []  # CSRF 등 세션 인증 비활성화

    def post(self, request):
        req = LoginRequestSerializer(data=request.data)
        if not req.is_valid():
            return Response({'ok': False, 'reason': 'invalidPayload', 'errors': req.errors},
                            status=status.HTTP_200_OK)

        loginId = req.validated_data['loginId']
        inputPassword = req.validated_data['password']

        user = getUserByLoginId(loginId)
        if user is None:
            res = LoginResultSerializer({'ok': False, 'reason': 'userNotFound'})
            return Response(res.data, status=status.HTTP_200_OK)

        # 비밀번호는 평문 비교 X → 해시 검증
        if not check_password(inputPassword, user.password):
            res = LoginResultSerializer({'ok': False, 'reason': 'wrongPassword'})
            return Response(res.data, status=status.HTTP_200_OK)

        profile = getProfileByUser(user)
        if profile is None:
            # 필요하면 자동 생성(선택)
            profile = Profile.objects.create(
                userId=user, profileName=user.username, profilePhoneNumber=''
            )

        res = LoginResultSerializer({
            'ok': True,
            'reason': '',
            'userId': user.id,
            'username': user.username,
            'profileName': profile.profileName,
            'profilePhoneNumber': profile.profilePhoneNumber
        })
        return Response(res.data, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []  # 완전 공개

    def get(self, request):
        # 지금은 권한 없음: 항상 anonymous 취급
        return Response({'ok': True, 'isAuthenticated': False, 'user': None}, status=status.HTTP_200_OK)
