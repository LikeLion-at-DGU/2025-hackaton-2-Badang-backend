from django.shortcuts import render
from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import *
from common.serializers import *
from .models import *
from .services import *
from .selectors import *

# Create your views here.

class CollaborationSearchListView(APIView):
    def post(self, request):
        
        req = CollaborationSearchReq(data=request.data)
        req.is_valid(raise_exception=True)
        
        type = req.validated_data["type"]
        category = req.validated_data["category"]
        query = req.validated_data["query"]
        storeId = req.validated_data["storeId"]
        
        try:
            res = getCollaborationSerach(storeId, type, category, query)
        except DomainError as e:
            return Response({"detail":str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        out = {
            "status":200,
            "message":"가까운 8개 가게 반환 완료",
            "data":{
                "store":res
            }
        }
        return Response(out, status=status.HTTP_200_OK)
        
class CollaborationPostView(APIView):
    
    def post(self, request):
        # 1) 입력 검증
        req = CollaborationCreateReq(data=request.data)
        req.is_valid(raise_exception=True)

        # 2) 컨텍스트에서 신청자 가게 ID 가져옴
        fromStoreId = req.validated_data["fromStoreId"]
        toStoreId = req.validated_data["toStoreId"]
        msg = req.validated_data.get("initialMessage", "")

        # 3) 서비스 호출(쓰기/도메인 로직)
        try:
            collab = createCollaboration(fromStoreId, toStoreId, msg)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        # 4) 응답 직렬화(응답 스펙 고정)
        
        out = {
            "status": 201,
            "message": "요청 성공",
            "collaborateId": collab.id,
            "IsAccepted":collab.isAccepted
        }
        return Response(out, status=status.HTTP_201_CREATED )


class CollaborationUpdateView(APIView):
    def patch(self, request):
        
        req = CollaborationMemoPatchReq(data=request.data)
        req.is_valid(raise_exception=True)
        
        collaborateId = req.validated_data["collaborateId"]
        storeId = req.validated_data["storeId"]
        msg = req.validated_data["memo"]
        
        
        try:
            memo = updateCollaborationMsg(collaborateId, storeId, msg)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        out = {
            "status": 200,
            "message": "조회 성공",
            "data": {
                "memo":memo
            }
        }
        return Response(out, status=status.HTTP_200_OK )

class CollaborationDeleteView(APIView):
    def delete(self, request, collaborationId: int):
        
        collaborationId = int(collaborationId)
        msg = deleteCollaboration(collaborationId)
        
        out = {
            "status": 200,
            "message": msg
        }
        
        return Response(out, status=status.HTTP_200_OK )
        
class ActiveCollaborationListView(APIView):
    def get(self, request, storeId: int):
        storeId = int(storeId)

        # (선택) 가게 존재 확인 로직이 필요하면 주석 해제
        # if not Store.objects.filter(id=store_id).exists():
        #     return Response({"status": 404, "message": "가게 없음", "data": {}},
        #                     status=status.HTTP_404_NOT_FOUND)

        rows = getActiveCollaboration(storeId)

        items = ActiveItem(rows, many=True, context={"storeId": storeId}).data
        out = {
            "status": 200,
            "message": "조회 성공",
            "data": {
                "collaborateStores": items
            }
        }
        return Response(out, status=status.HTTP_200_OK)
    
class RequestCollaborateListView(APIView):
    def get(self, request, storeId:int):
        storeId = int(storeId)
        
        rows = getRequestCollaboration(storeId)
        items = OutgoingItem(rows, many=True).data
        
        out = {
            "status": 200,
            "message": "조회 성공",
            "data": {
                "requestStores": items
            }
        }
        return Response(out, status=status.HTTP_200_OK)
    
    
class ResponseCollaborateListView(APIView):
    def get(self, request, storeId:int):
        storeId = int(storeId)
        
        rows = getResponseCollaboration(storeId)
        items = IncomingItem(rows, many=True).data
        
        out = {
            "status": 200,
            "message": "조회 성공",
            "data": {
                "responsetStores": items
            }
        }
        return Response(out, status=status.HTTP_200_OK)
    
class CollaborateDecisionView(APIView):
    def patch(self, request):
        req = CollaborationDecisionReq(data=request.data)
        req.is_valid(raise_exception=True)
        
        collaborateId = req.validated_data["collaborateId"]
        isAccepted = req.validated_data["isAccepted"]
        
        msg = decisionCollaboration(collaborateId, isAccepted)
        
        out = {
            "status":200,
            "message":msg
        }
        return Response(out, status=status.HTTP_200_OK)