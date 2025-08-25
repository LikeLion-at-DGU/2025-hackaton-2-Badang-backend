from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import StoreReviewResponseSerializer # 응답 포장용 시리얼라이저
from main.models import Store
from .services import *
from rest_framework.permissions import AllowAny, IsAuthenticated
from common.serializers import CommonResponseSerializer
from .selectors import getReviewAnalysis
from main.serializers import ProfileSerializer

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
    # retrieve, create 등 다른 메서드 필요 시 추가