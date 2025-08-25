from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.decorators import action
from .serializers import StoreReviewResponseSerializer # 응답 포장용 시리얼라이저
from main.models import Store
from .services import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from common.serializers import CommonResponseSerializer
from .selectors import getReviewAnalysis
from main.serializers import ProfileSerializer
from .models import ReviewAnalysis
from django.utils import timezone
import logging
import threading

logger = logging.getLogger(__name__)

# 리뷰 생성 로직 main으로 이동. 리뷰 데이터를 읽는 로직만 남김.
class ReviewAnalysisViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]
    
    def list(self, request):
        # 쿼리 파라미터에서 storeId와 term을 가져옴
        user = request.user.profile
        term_str = request.query_params.get('term')

        # 파라미터 유효성 검사
        if not term_str:
            return Response({
                "error": "BadRequest",
                "message": "요청에 term이 누락되었습니다.",
                "statusCode": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            storeId = user.stores.first().id
            term = int(term_str)
            
        except (ValueError, TypeError):
            return Response({
                "error": "BadRequest",
                "message": "user의 가게가 존재하지 않거나 term 값이 유효하지 않은 숫자입니다.",
                "statusCode": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        # 로그인/회원가입 시 생성된 리뷰 분석 데이터 조회.
        analysisData = getReviewAnalysis(storeId, term)
        userData = ProfileSerializer(user, context={"request": request}).data
        # 리스폰스 반환
        responseData = {
            "statusCode": 200,
            "message": "리뷰분석 조회 성공",
            "data": analysisData,
            "user":userData
        }

        return Response(responseData, status=status.HTTP_200_OK)
    
    def create(self, request):
        """로그인 시 리뷰 분석 데이터 확인 및 생성"""
        try:
            user = request.user.profile
            store = user.stores.first()
            
            if not store:
                return Response({
                    "error": "NoStore",
                    "message": "등록된 가게가 없습니다.",
                    "statusCode": 404
                }, status=status.HTTP_404_NOT_FOUND)
            
            logger.info(f"Checking review analysis for store: {store.id}, name: {store.name}")
            
            # 기존 분석 데이터 확인
            existing_analyses = ReviewAnalysis.objects.filter(storeId=store)
            
            should_create_analysis = False
            
            if existing_analyses.count() == 0:
                logger.info("No existing analyses found. Will create new ones...")
                should_create_analysis = True
            else:
                latest_analysis = existing_analyses.order_by('-updatedAt').first()
                if latest_analysis:
                    days_since_update = (timezone.now() - latest_analysis.updatedAt).days
                    logger.info(f"Latest analysis updated {days_since_update} days ago")
                    
                    if days_since_update > 3:
                        logger.info("Analysis is older than 3 days. Will create new ones...")
                        should_create_analysis = True
                    else:
                        logger.info("Analysis is recent. No need to update.")
                        return Response({
                            "message": "최근 분석이 존재합니다.",
                            "status": "recent",
                            "lastUpdated": latest_analysis.updatedAt,
                            "statusCode": 200
                        }, status=status.HTTP_200_OK)
            
            if should_create_analysis:
                def create_analysis():
                    try:
                        logger.info("Starting review analysis...")
                        postReviewAnalysis(store.id, term=0)
                        postReviewAnalysis(store.id, term=1)
                        logger.info("Review analysis completed")
                    except Exception as e:
                        logger.error(f"Review analysis failed: {e}")
                
                # 백그라운드에서 실행
                thread = threading.Thread(target=create_analysis)
                thread.daemon = True
                thread.start()
                logger.info("Analysis thread started")
                
                return Response({
                    "message": "리뷰 분석이 시작되었습니다.",
                    "status": "analyzing",
                    "storeId": store.id,
                    "estimatedTime": "약 30초 소요",
                    "statusCode": 202
                }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"Error in review analysis creation: {e}")
            return Response({
                "error": "ServerError",
                "message": "서버 오류가 발생했습니다.",
                "statusCode": 500
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    # retrieve, create 등 다른 메서드 필요 시 추가