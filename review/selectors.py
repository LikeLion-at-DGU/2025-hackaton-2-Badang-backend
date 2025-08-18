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
