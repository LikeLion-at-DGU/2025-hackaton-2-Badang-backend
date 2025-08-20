from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import StoreReviewResponseSerializer # 응답 포장용 시리얼라이저
from main.models import Store
from .services import *

class ReviewAnalysisViewSet(viewsets.ViewSet):
    def list(self, request):
        # 쿼리 파라미터에서 storeId와 term을 가져옴
        store_id_str = request.query_params.get('storeId')
        term_str = request.query_params.get('term')

        # 파라미터 유효성 검사
        if not store_id_str or not term_str:
            return Response({
                "error": "BadRequest",
                "message": "요청에 storeId 또는 term이 누락되었습니다.",
                "statusCode": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        try:
            store_id = int(store_id_str)
            term = int(term_str)
        except (ValueError, TypeError):
            return Response({
                "error": "BadRequest",
                "message": "storeId 또는 term 값이 유효하지 않은 숫자입니다.",
                "statusCode": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        # OpenAI 활용 리뷰 분석 생성 -> 시리얼라이저로 옮길 예정
        analysis_data = getReviewAnalysis(store_id, term)

        # 에러 파싱
        if analysis_data is None:
            return Response({
                "error": "NotFound",
                "message": "해당 가게를 찾을 수 없습니다.",
                "statusCode": 404
            }, status=status.HTTP_404_NOT_FOUND)

        # 리스폰스 반환
        response_data = {
            "statusCode": 200,
            "message": "프롬프트 검색 성공",
            "data": analysis_data
        }

        return Response(response_data, status=status.HTTP_200_OK)
    
    # retrieve, create 등 다른 메서드 필요 시 추가