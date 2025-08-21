from django.shortcuts import render
from django.shortcuts import get_object_or_404, get_list_or_404
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .serializers import *
from common.serializers import *
from .models import *
from .services import *
from .selectors import *

# Create your views here.

class CollaborationSearchListView(APIView):
    permission_classes = [IsAuthenticated]
    
    
    def post(self, request):
        
        req = CollaborationSearchReq(data=request.data)
        req.is_valid(raise_exception=True)
        
        type = req.validated_data["type"]
        category = req.validated_data["category"]
        query = req.validated_data["query"]
        
        user = request.user.profile
        
        try:
            res = getCollaborationSearch(user, type, category, query)
        except DomainError as e:
            return Response({"detail":str(e)}, status=status.HTTP_400_BAD_REQUEST)
        
        stores = CollaborationSearchRes(res, many=True)
        
        out = {
            "status":200,
            "message":"가까운 8개 가게 반환 완료",
            "data":{
                "store":stores.data
            }
        }
        return Response(out, status=status.HTTP_200_OK)
        
class CollaborationPostView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        
        req = CollaborationCreateReq(data=request.data)
        req.is_valid(raise_exception=True)
        
        user = request.user.profile

        toStoreId = req.validated_data["toStoreId"]
        msg = req.validated_data.get("initialMessage", "")

        
        try:
            collab = createCollaboration(user, toStoreId, msg)
        except DomainError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)

        
        
        out = {
            "status": 201,
            "message": "요청 성공",
            "collaborateId": collab.id,
            "IsAccepted":collab.isAccepted
        }
        return Response(out, status=status.HTTP_201_CREATED )


class CollaborationUpdateView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        
        req = CollaborationMemoPatchReq(data=request.data)
        req.is_valid(raise_exception=True)
        
        user = request.user.profile
        
        collaborateId = req.validated_data["collaborateId"]
        msg = req.validated_data["memo"]
        
        
        try:
            memo = updateCollaborationMsg(collaborateId, user, msg)
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
    permission_classes = [IsAuthenticated]
    
    def delete(self, request, collaborateId: int):
        
        user = request.user.profile
        
        collaborateId = int(collaborateId)
        msg = deleteCollaboration(collaborateId,user)
        
        out = {
            "status": 200,
            "message": msg
        }
        
        return Response(out, status=status.HTTP_200_OK )
        
class ActiveCollaborationListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        
        user = request.user.profile

        rows = getActiveCollaboration(user)

        items = ActiveItem(rows, many=True, context={"storeId": user.stores.first().id}).data
        out = {
            "status": 200,
            "message": "조회 성공",
            "data": {
                "collaborateStores": items
            }
        }
        return Response(out, status=status.HTTP_200_OK)
    
class RequestCollaborateListView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user.profile
        
        rows = getRequestCollaboration(user)
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
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        user = request.user.profile
        
        rows = getResponseCollaboration(user)
        items = IncomingItem(rows, many=True).data
        
        out = {
            "status": 200,
            "message": "조회 성공",
            "data": {
                "responseStores": items
            }
        }
        return Response(out, status=status.HTTP_200_OK)
    
class CollaborateDecisionView(APIView):
    permission_classes = [IsAuthenticated]
    
    def patch(self, request):
        user = request.user.profile
        
        req = CollaborationDecisionReq(data=request.data)
        req.is_valid(raise_exception=True)
        
        collaborateId = req.validated_data["collaborateId"]
        isAccepted = req.validated_data["isAccepted"]
        
        msg = decisionCollaboration(collaborateId, isAccepted, user)
        
        out = {
            "status":200,
            "message":msg
        }
        return Response(out, status=status.HTTP_200_OK)