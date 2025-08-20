
from .llm import run_llm
def analyze_reviews(keyword : str) -> dict:
    system = (
        "보낸 키워드에 맞는 이미지를 제작해줘"
    )
    user = {"keyword":keyword}
    import json
    return json.loads(run_llm(system, user))
