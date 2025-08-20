from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from .serializers import *
from .services import *
from .models import *
from main.models import Store


class DomainError(Exception):
    pass


class TrendsToKeywordView(APIView):
    def post(self, request):
        
        req = TrendInputReq(data=request.data)
        req.is_valid(raise_exception=True)

        trend = saveSingleKeywordToDB(req.validated_data["trends"])
        out = TrendRes(trend, context={"request": request})
        return Response(out.data, status=status.HTTP_201_CREATED)

class CreateKeywordView(APIView):
    def post(self, request):
        
        req = KeywordsInputReq(data = request.data)
        req.is_valid(raise_exception=True)
        
        storeId = req.validated_data["storeId"]
        
        keyword = req.validated_data["keyword"]
        store = Store.objects.get(id=storeId)
        
        try:
            store = Store.objects.get(id=storeId)  # get()으로 변경
            res = keywordSaveByUserSimple(keyword, store)
            
            out = KeywordRes(res)  # 실제 생성된 키워드 정보 반환
            return Response(out.data, status=status.HTTP_201_CREATED)
            
        except Store.DoesNotExist:
            return Response({"detail": "스토어를 찾을 수 없습니다."}, status=status.HTTP_404_NOT_FOUND)
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": "키워드 생성에 실패했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class GetTrendApi(APIView):
    def get(self, request, trend_id):
        trend = get_object_or_404(Trend, id=trend_id)
        out = TrendRes(trend, context={"request": request})
        return Response(out.data)