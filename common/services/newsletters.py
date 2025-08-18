# ai/services/newsletter.py
from .llm import run_llm
def build_newsletter(store_profile: dict, trend_top3: list, review_summary: dict) -> dict:
    system = (
        "너는 소상공인 마케팅 어드바이저다. 입력(가게 정보, 트렌드 3개, 리뷰 요약)을 바탕으로 "
        "모바일 친화 HTML 뉴스레터를 생성하라. JSON으로만 답하라: "
        "{\"subject\":\"\",\"html\":\"\",\"summary\":{\"selected_trends\":[],\"cta\":[\"...\"]}}"
    )
    user = {
        "store": store_profile,
        "trends": trend_top3,
        "review_overview": review_summary.get("overview"),
    }
    import json
    return json.loads(run_llm(system, user))