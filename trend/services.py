# trend/services.py
import json
from django.db import transaction
from .models import Trend

@transaction.atomic
def save_seed_keywords_to_db(keywords: list[str]) -> Trend:
    if not isinstance(keywords, list):
        raise ValueError("keywords must be a list")

    # 정제(옵션): 공백 제거 + 빈 문자열 제거 + 중복 제거
    cleaned = []
    for s in keywords:
        if isinstance(s, str):
            ss = s.strip()
            if ss:
                cleaned.append(ss)
    deduped = list(dict.fromkeys(cleaned))

    # trendData에는 **키워드 배열만** 저장
    return Trend.objects.create(
        trendData=json.dumps(deduped, ensure_ascii=False)
    )
