from django.shortcuts import render
from rest_framework import viewsets, mixins
from django.db import transaction
from .models import *
from .serializers import *

from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
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