# review/views.py
from rest_framework import viewsets, status, mixins
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from .serializers import StoreReviewResponseSerializer
from .selectors import get_store_analysis_data

class ReviewAnalysisViewSet(viewsets.ViewSet, mixins.ListModelMixin):
    @action(detail=False, methods=['GET'])
    def get_analysis(self, request):
        store_id = request.query_params.get('storeId')
        term = request.query_params.get('term')

        # term은 문자열로 넘어오므로 정수형으로 변환
        try:
            term = int(term)
        except (ValueError, TypeError):
            return Response({
                "error": "BadRequest",
                "message": "term 값이 유효하지 않습니다.",
                "statusCode": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        if not all([store_id is not None, term is not None]):
            return Response({
                "error": "BadRequest",
                "message": "요청에 storeId 또는 term이 누락되었습니다.",
                "statusCode": 400
            }, status=status.HTTP_400_BAD_REQUEST)

        analysis_data = get_store_analysis_data(store_id, term)

        if analysis_data is None:
            return Response({
                "error": "NotFound",
                "message": "해당 가게를 찾을 수 없습니다.",
                "statusCode": 404
            }, status=status.HTTP_404_NOT_FOUND)

        response_data = {
            "statusCode": 200,
            "message": "프롬프트 검색 성공",
            "data": analysis_data
        }

        serializer = StoreReviewResponseSerializer(data=response_data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    



# Public test endpoint (no auth) to quickly verify the analysis API in Postman/curl.
@api_view(['GET'])
@permission_classes([AllowAny])
def ping_analysis(request):
    store_id = request.query_params.get('storeId')
    term = request.query_params.get('term')

    try:
        term = int(term) if term is not None else 1
    except (ValueError, TypeError):
        return Response({
            "error": "BadRequest",
            "message": "term 값이 유효하지 않습니다.",
            "statusCode": 400
        }, status=status.HTTP_400_BAD_REQUEST)

    if store_id is None:
        return Response({
            "error": "BadRequest",
            "message": "요청에 storeId가 누락되었습니다.",
            "statusCode": 400
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        store_id_int = int(store_id)
    except (ValueError, TypeError):
        return Response({
            "error": "BadRequest",
            "message": "storeId 값이 유효하지 않습니다.",
            "statusCode": 400
        }, status=status.HTTP_400_BAD_REQUEST)

    analysis_data = get_store_analysis_data(store_id_int, term)
    if analysis_data is None:
        return Response({
            "error": "NotFound",
            "message": "해당 가게를 찾을 수 없습니다.",
            "statusCode": 404
        }, status=status.HTTP_404_NOT_FOUND)

    return Response({
        "statusCode": 200,
        "message": "프롬프트 검색 성공",
        "data": analysis_data
    }, status=status.HTTP_200_OK)