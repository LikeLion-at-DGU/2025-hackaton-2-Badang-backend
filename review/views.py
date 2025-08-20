# review/views.py (수정 제안)

from rest_framework import viewsets, status
from rest_framework.response import Response
from .serializers import StoreReviewResponseSerializer # 응답 포장용 시리얼라이저
from main.models import Store
from .services import * # 우리가 만든 핵심 서비스 함수

class ReviewAnalysisViewSet(viewsets.ViewSet):
    """
    리뷰 분석 데이터를 처리하는 ViewSet.
    list 메서드가 'GET /review/analysis?storeId=...&term=...' 요청을 처리합니다.
    """
    def list(self, request):
        # 1. 쿼리 파라미터에서 storeId와 term을 가져옵니다.
        store_id_str = request.query_params.get('storeId')
        term_str = request.query_params.get('term')

        # 2. 파라미터 유효성 검증
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

        # 3. 핵심 로직을 담고 있는 서비스 계층 호출
        analysis_data = getReviewAnalysis(store_id, term)

        # 4. 서비스 결과에 따른 분기 처리 (API 명세서에 맞게)
        if analysis_data is None:
            return Response({
                "error": "NotFound",
                "message": "해당 가게를 찾을 수 없습니다.",
                "statusCode": 404
            }, status=status.HTTP_404_NOT_FOUND)

        # 5. 최종 응답 포장 및 반환
        response_data = {
            "statusCode": 200,
            "message": "프롬프트 검색 성공",
            "data": analysis_data
        }

        # 응답 형식을 검증하고 싶다면 Serializer를 사용할 수 있습니다.
        # serializer = StoreReviewResponseSerializer(data=response_data)
        # serializer.is_valid(raise_exception=True)
        # return Response(serializer.validated_data, status=status.HTTP_200_OK)
        
        return Response(response_data, status=status.HTTP_200_OK)
    
    # retrieve, create 등 다른 메서드가 필요하다면 여기에 추가...