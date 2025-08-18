# ai/services/reviews.py
from .llm import run_llm
def analyze_reviews(store_id: int, reviews: list[dict]) -> dict:
    system = (
        "너는 리뷰 분석가다. 각 리뷰에 대해 sentiment(positive|neutral|negative), "
        "sarcasm(true|false), aspects(위생/가격/응대/맛/대기 등), "
        "사장님 개선 제안(문장) 배열을 추출하라. "
        "JSON으로만 답하라: {\"overview\":{...}, \"per_review\":[{...}]}"
    )
    user = {"store_id": store_id, "reviews": reviews}
    import json
    return json.loads(run_llm(system, user))
