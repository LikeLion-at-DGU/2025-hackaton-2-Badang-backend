# ai/services/trends.py
from .llm import run_llm
def extract_trends(trend_payload: dict) -> dict:
    system = (
        "너는 마케팅 리서처다. 입력된 최근 구글 트렌드 데이터를 분석해서 "
        "상업적 활용가치 높은 키워드 3개와 선정 이유, 아이디어 2개를 제시하라. "
        "JSON으로만 답하라: {\"top3\":[{\"keyword\":\"\",\"reason\":\"\",\"ideas\":[\"\",\"\"]}]}"
    )
    user = {"data": trend_payload}
    text = run_llm(system, user)
    # text는 JSON 문자열일 것이므로 파싱 후 DB에 저장
    import json
    return json.loads(text)
