from django.shortcuts import render
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import *
from common.serializers import *
from .models import *
from .services import *

# Create your views here.

class CollaborationCreateView(APIView):
    
    def post(self, request):
        # 1) 입력 검증
        request = CollaborationCreateReq(data=request.data)
        request.is_valid(raise_exception=True)

        # 2) 컨텍스트에서 신청자 가게 ID 가져옴
        fromStoreId = request.validated_data["fromStoreId"]
        toStoreId = request.validated_data["toStoreId"]
        msg = request.validated_data.get("initialMessage", "")

        # 3) 서비스 호출(쓰기/도메인 로직)
        try:
            collab = createCollaboration(fromStoreId, toStoreId, msg)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 4) 응답 직렬화(응답 스펙 고정)
        out = {
            "collaborateId": collab.id,
            "status": "PENDING" if collab.isAccepted == Collaborate.Status.PENDING else "UNKNOWN",
        }
        return Response(CollaborationCreatedResp(out).data, status=status.HTTP_201_CREATED)
