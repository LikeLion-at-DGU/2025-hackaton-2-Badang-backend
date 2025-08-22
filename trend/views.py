from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated

from .serializers import *
from newsletter.serializers import NewsletterSerializer
from .services import *
from newsletter.selectors import getNewsletterDetail
from .models import *
from main.models import Store
from newsletter.views import createNewsletter
from newsletter.services import createNewsletterByUser


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
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        
        user = request.user.profile
        me = user.stores.first()
        
        if me is None:
            raise DomainError("request 를 보낸 유저에게는 가게가 없습니다.")
        
        req = KeywordsInputReq(data = request.data)
        req.is_valid(raise_exception=True)
        
        keyword = req.validated_data["keyword"]
        
        try: 
            res = keywordSaveByUserSimple(keyword, me)
            
        except ValueError as e:
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"detail": "키워드 생성에 실패했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        try:
            out = KeywordRes(res)  # 실제 생성된 키워드 정보 반환
            print(keyword)
            
            news = createNewsletterByUser(me.id, res)
            serializer = NewsletterSerializer(news, context={'request': request})

            responseData = {
                "message": "뉴스레터 상세 정보를 성공적으로 조회하였습니다.",
                "statusCode": 200,
                "data": serializer.data
            }

            return Response(responseData, status=status.HTTP_200_OK)
            
        except Exception as e:
            print(keyword)
            
            return Response({"detail":"뉴스레터 생성에 실패했습니다."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
class GetTrendApi(APIView):
    def get(self, request, trend_id):
        trend = get_object_or_404(Trend, id=trend_id)
        out = TrendRes(trend, context={"request": request})
        return Response(out.data)