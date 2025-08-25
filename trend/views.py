from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from rest_framework.permissions import AllowAny, IsAuthenticated
import logging

from .serializers import *
from newsletter.serializers import NewsletterSerializer
from .services import *
from .models import *
from newsletter.services import createNewsletterByUser, createNewsletter

logger = logging.getLogger(__name__)


class DomainError(Exception):
    pass


class TrendsToKeywordView(APIView):
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        
        req = TrendInputReq(data=request.data)
        req.is_valid(raise_exception=True)

        trend, _ = saveKeywordsFromTrends(req.validated_data["trends"])

        # 커밋 이후 DB에서 다시 읽기 (키워드 프리패치)
        trendRefetched = Trend.objects.prefetch_related("keywords").get(id=trend.id)

        trendOut = TrendRes(trendRefetched, context={"request": request}).data
        # 굳이 바깥으로 keywords를 중복 노출할 필요 없으면 trendOut만 내려도 OK
        return Response(
            {
                "message": "트렌드와 키워드가 생성되었습니다.",
                "statusCode": 201,
                "data": {
                    "trend": trendOut,
                    "keywords": trendOut["keywords"],  # 필요 없으면 이 라인은 삭제해도 됨
                },
            },
            status=status.HTTP_201_CREATED,
        )
        
    
        
class CreateKeywordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        logger.info(f"CreateKeywordView POST request from user: {request.user.id if request.user.is_authenticated else 'Anonymous'}")
        logger.info(f"Request data: {request.data}")
        
        try:
            # 사용자 프로필 확인
            try:
                user = request.user.profile
                logger.info(f"User profile found: {user.profileName}")
            except Exception as e:
                logger.error(f"Profile access error for user {request.user.id}: {str(e)}")
                return Response({
                    "detail": f"사용자 프로필을 찾을 수 없습니다: {str(e)}"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # 사용자 가게 확인
            me = user.stores.first()
            if me is None:
                logger.warning(f"No store found for user {user.profileName}")
                return Response({
                    "detail": "request 를 보낸 유저에게는 가게가 없습니다."
                }, status=status.HTTP_400_BAD_REQUEST)
            else:
                logger.info(f"Store found: {me.name}")
                
        except Exception as e:
            logger.error(f"User authentication error: {str(e)}")
            return Response({
                "detail": f"사용자 인증 처리 중 오류가 발생했습니다: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 요청 데이터 검증
        req = KeywordsInputReq(data=request.data)
        if not req.is_valid():
            return Response({
                "detail": f"요청 데이터가 유효하지 않습니다: {req.errors}"
            }, status=status.HTTP_400_BAD_REQUEST)
            
        keyword = req.validated_data["keyword"]
        if not keyword or not keyword.strip():
            return Response({
                "detail": "키워드를 입력해주세요."
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            # 키워드 생성
            logger.info(f"Creating keyword: {keyword}")
            kw = keywordSaveByUserSync(keyword, me)
            logger.info(f"Keyword created with status: {kw.status}")

            if kw.status != "succeeded" or not kw.keywordImageUrl:
                logger.error(f"Keyword image generation failed. Status: {kw.status}, Image URL: {kw.keywordImageUrl}")
                return Response({
                    "detail": "키워드 이미지 생성에 실패했습니다.",
                    "keyword_status": kw.status
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 뉴스레터 생성
            try:
                logger.info(f"Creating newsletter for store {me.id} with keyword {kw.id}")
                news = createNewsletterByUser(me.id, kw)
                logger.info(f"Newsletter created successfully: {news.newsId}")
            except Exception as newsletter_error:
                logger.error(f"Newsletter creation failed: {str(newsletter_error)}")
                return Response({
                    "detail": f"뉴스레터 생성에 실패했습니다: {str(newsletter_error)}"
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                
        except ValueError as e:
            logger.error(f"ValueError in keyword creation: {str(e)}")
            return Response({"detail": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Unexpected error in keyword creation: {str(e)}")
            return Response({
                "detail": f"키워드 생성에 실패했습니다: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # 응답 직렬화만
        kwData = KeywordRes(kw).data
        newsData = NewsletterSerializer(news, context={'request': request}).data

        return Response({
            "message": "키워드와 뉴스레터를 생성했습니다.",
            "statusCode": 200,
            "data": {
                "keyword": kwData,
                "newsletter": newsData
            }
        }, status=status.HTTP_200_OK)


class GetTrendApi(APIView):
    def get(self, request, trend_id):
        trend = get_object_or_404(Trend, id=trend_id)
        out = TrendRes(trend, context={"request": request})
        return Response(out.data)