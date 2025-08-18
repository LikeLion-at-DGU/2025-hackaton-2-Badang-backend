from typing import Dict, List, Optional
from django.core.exceptions import ObjectDoesNotExist
from django.forms.models import model_to_dict

from review.models import ReviewAnalysis
from main.models import Store


def getReviewAnalysis(analysis: ReviewAnalysis) -> Dict:

    # model_to_dict is convenient but may include related objects; pick explicit fields.
    return {
        'id': analysis.id,
        'store_id': analysis.store_id if hasattr(analysis, 'store_id') else getattr(analysis.store, 'id', None),
        'summary': getattr(analysis, 'summary', ''),
        'score': getattr(analysis, 'score', None),
        'topics': getattr(analysis, 'topics', []),
        'sentiment': getattr(analysis, 'sentiment', None),
        'updated_at': getattr(analysis, 'updated_at', None),
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

from datetime import datetime, timedelta
from typing import Dict, Any

def get_store_analysis_data(store_id: int, term: int) -> Dict[str, Any]:
    """
    주어진 가게 ID와 기간에 따른 분석 데이터를 반환합니다.

    Args:
        store_id (int): 가게의 고유 ID.
        term (int): 분석 기간 (0: 전체, 1: 한 달, 2: 일주일).

    Returns:
        Dict[str, Any]: 분석 데이터 딕셔너리.
    """
    # API 연결 확인용 하드코딩 데이터
    # 가게 정보 조회
    if store_id != 1:
        # 가상의 가게 없음 에러 발생
        return None  # 또는 적절한 에러 핸들링

    store_name = "서브웨이 충무로점"

    # 기간에 따른 데이터 가공 로직 (예시)
    if term == 0:
        good_percentage = 65.0
        middle_percentage = 15.0
        bad_percentage = 20.0
        analysis_keyword = "서비스, 청결"
        analysis_problem = "일부 손님들이 서비스 불만에 대해 언급하고 있습니다."
        analysis_solution = "직원 교육을 통해 서비스 품질을 개선해야 합니다."
    elif term == 1:
        good_percentage = 59.6
        middle_percentage = 10.4
        bad_percentage = 30.0
        analysis_keyword = "불친절이라는 단어가 자주 등장하네요!"
        analysis_problem = "불친절하다는 건 직원 교육..."
        analysis_solution = "직원 교육/손님응대에 신경 쓰시면...."
    elif term == 2:
        good_percentage = 70.0
        middle_percentage = 10.0
        bad_percentage = 20.0
        analysis_keyword = "맛있다, 신선하다"
        analysis_problem = "특별한 문제점은 보이지 않습니다."
        analysis_solution = "현재의 긍정적인 평가를 유지하기 위해 지속적으로 노력해야 합니다."
    else:
        # 유효하지 않은 term 값 처리
        return None

    return {
        "storeName": store_name,
        "goodPoint": "집에서 가깝고 맛있어요",
        "badPoint": "직원이 불친절해요",
        "percentage": {
            "goodPercentage": good_percentage,
            "middlePercentage": middle_percentage,
            "badPercentage": bad_percentage
        },
        "analysisKeyword": analysis_keyword,
        "analysisProblem": analysis_problem,
        "analysisSolution": analysis_solution,
    }