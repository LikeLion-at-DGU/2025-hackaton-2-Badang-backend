from django.shortcuts import render
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied, NotFound

from .selectors import getNewsletterList
from .serializers import NewsletterListResponseSerializer
from .models import NewsLetter
from main.models import Store, Profile

# Create your views here.
class NewsletterViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        # 스토어 id 파라마터 추출 및 유효성 검사
        storeId_str = request.query_params.get('storeId')
        
        if not storeId_str:
            return Response(
                {"error":"BadRequest","message":"storeId 값이 필요합니다.","statusCode":400},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 프로필, 가게 정보 검사
        try:
            storeId = int(storeId_str)
            userProfile = request.user.profile
            store = Store.objects.get(id=storeId, user=userProfile)
        except (ValueError, TypeError):
            return Response({
                "error": "BadRequest",
                "message": "storeId 값이 유효하지 않은 숫자입니다.",
                "statusCode": 400
            }, status=status.HTTP_400_BAD_REQUEST)
            
        except Store.DoesNotExist:
            return Response({
                "error": "NotFound",
                "message": "해당 가게를 찾을 수 없습니다.",
                "statusCode": 404
            }, status=status.HTTP_404_NOT_FOUND)
            
        # 페이지네이션 파라미터 처리
        try:
            cursor = request.query_params.get('cursor')
            cursor = int(cursor) if cursor is not None else None
            limit = int(request.query_params.get('limit', 9))
            
        except (ValueError, TypeError):
            return Response({
                "error": "BadRequest",
                "message": "cursor 또는 limit 값이 유효하지 않습니다.",
                "statusCode": 400
            }, status=status.HTTP_400_BAD_REQUEST)
            
        # selectors.py 호출. 뉴스레터 GET
        newsletters, hasMore = getNewsletterList(store=store, cursor=cursor, limit=limit)
        
        # 리스폰스 반환
        dataSerializer = NewsletterListResponseSerializer(newsletters, many=True)
        return Response({
            "message": "뉴스레터 목록 조회 성공"
            "data": dataSerializer.data,
            "hasMore": hasMore
        })