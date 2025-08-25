from typing import Dict, List, Optional, Any
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict

from review.models import ReviewAnalysis
from main.models import Store


def getReviewAnalysis(storeId: int, term: int) -> Dict:
    try:
        analysis = ReviewAnalysis.objects.get(storeId=storeId, term=term) # 스토어 아이디 / term 기반 리뷰 분석 조회
        
    except ReviewAnalysis.DoesNotExist:
        return {
            "error": "Not Found",
            "message": f"Store ID {storeId}에 대한 분석 결과가 없습니다.",
            "status": 404
        }
    return {
        'storeName': analysis.storeName,
	    "goodPoint": analysis.goodPoint,
	    "badPoint": analysis.badPoint,
	    "percentage": {
		    "goodPercentage": analysis.goodPercentage,
		    "middlePercentage": analysis.middlePercentage,
		    "badPercentage": analysis.badPercentage
	    },
	    "analysisKeyword": analysis.analysisKeyword,
	    "analysisProblem": analysis.analysisProblem,
	    "analysisSolution": analysis.analysisSolution
    }

def get_analysis_by_store(store_id: int) -> Optional[Dict]:
    """Return a single analysis dict for the given store_id, or None if not found."""
    try:
        analysis = ReviewAnalysis.objects.get(store_id=store_id)
        return getReviewAnalysis(analysis)
    except ObjectDoesNotExist:
        return None


def list_analyses_for_stores(store_ids: List[int]) -> List[Dict]:
    qs = ReviewAnalysis.objects.filter(store_id__in=store_ids)
    mapping = {a.store_id: a for a in qs}
    results: List[Dict] = []
    for sid in store_ids:
        a = mapping.get(sid)
        if a:
            results.append(getReviewAnalysis(a))
    return results


def get_or_create_stub_for_store(store_id: int) -> Dict:

    ana = get_analysis_by_store(store_id)
    if ana:
        return ana
    return {
        'id': None,
        'store_id': store_id,
        'summary': '',
        'score': None,
        'topics': [],
        'sentiment': None,
        'updated_at': None,
    }

# from datetime import datetime, timedelta
# from typing import Dict, Any

# def get_store_analysis_data(store_id: int, term: int) -> Dict[str, Any]:
#     """
#     주어진 가게 ID와 기간에 따른 분석 데이터를 반환합니다.

#     Args:
#         store_id (int): 가게의 고유 ID.
#         term (int): 분석 기간 (0: 전체, 1: 한 달, 2: 일주일).

#     Returns:
#         Dict[str, Any]: 분석 데이터 딕셔너리.
#     """
#     # API 연결 확인용 하드코딩 데이터
#     # 가게 정보 조회
#     if store_id != 1:
#         # 가상의 가게 없음 에러 발생
#         return None  # 또는 적절한 에러 핸들링

#     store_name = "서브웨이 충무로점"

#     # 기간에 따른 데이터 가공 로직 (예시)
#     if term == 0:
#         return {
#             "storeName": store_name,
#             "goodPoint": "신선한 재료가 많아요",
#             "badPoint": "직원이 자주 바뀌어요",
#             "percentage": {
#                 "goodPercentage": 65.0,
#                 "middlePercentage": 15.0,
#                 "badPercentage": 20.0
#             },
#             "analysisKeyword": "서비스, 청결",
#             "analysisProblem": "일부 고객들이 서비스에 불만을 표현합니다.",
#             "analysisSolution": "직원 교육을 강화하고 매장 청결을 유지하세요."
#         }
#     elif term == 1:
#         return {
#             "storeName": store_name,
#             "goodPoint": "집에서 가깝고 맛있어요",
#             "badPoint": "직원이 불친절해요",
#             "percentage": {
#                 "goodPercentage": 59.6,
#                 "middlePercentage": 10.4,
#                 "badPercentage": 30.0
#             },
#             "analysisKeyword": "불친절이라는 단어가 자주 등장하네요!",
#             "analysisProblem": "불친절하다는 건 직원 교육이 필요하다는 뜻입니다.",
#             "analysisSolution": "직원 교육/손님응대 개선에 집중하세요."
#         }
#     elif term == 2:
#         return {
#             "storeName": store_name,
#             "goodPoint": "맛있고 신선해요",
#             "badPoint": "좌석이 부족해요",
#             "percentage": {
#                 "goodPercentage": 70.0,
#                 "middlePercentage": 10.0,
#                 "badPercentage": 20.0
#             },
#             "analysisKeyword": "맛있다, 신선하다",
#             "analysisProblem": "특별한 문제점은 크게 보이지 않습니다.",
#             "analysisSolution": "긍정적인 평가를 유지하세요."
#         }
#     else:
#         # 유효하지 않은 term 값 처리
#         return None
