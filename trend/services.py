# trend/services.py
import json
from django.db import transaction
from .models import *
from openai import OpenAI
import boto3
from common.services.images import *

import base64, hashlib
from django.core.files.base import ContentFile
from django.core.files.storage import default_storage
from django.conf import settings



@transaction.atomic
def save_seed_keywords_to_db(keywords: list[str]) -> Trend:
    if not isinstance(keywords, list):
        raise ValueError("keywords must be a list")

    # 1) 정제 + 중복 제거
    cleaned = []
    for s in keywords:
        if isinstance(s, str):
            ss = s.strip()
            if ss:
                cleaned.append(ss)
    deduped = list(dict.fromkeys(cleaned))

    # 2) Trend 저장 (키워드 배열은 trend.trendData에 JSON으로)
    trend = Trend.objects.create(
        trendData=json.dumps(deduped, ensure_ascii=False)
    )

    # 3) Keyword 행 생성: 우선 pending 상태로 bulk_create
    kw_objs = [
        Keyword(
            keywordName=name,
            trend=trend,
            status="pending",
            isImage=False,
            isCreatedByUser=False,
        )
        for name in deduped
    ]
    Keyword.objects.bulk_create(kw_objs)

    # 4) 트랜잭션 커밋 후 이미지 생성(외부 호출) → DB 업데이트
    def _after_commit_generate():
        for kw in Keyword.objects.filter(trend=trend, status="pending"):
            try:
                rel_path = generate_local_image_for_keyword(kw.keywordName, size="512x512")
                # 상대경로 → URL
                # 예: trends/xxx.png -> /media/trends/xxx.png
                url = settings.MEDIA_URL.rstrip("/") + "/" + rel_path.lstrip("/")
                kw.keywordImageUrl = url
                kw.isImage = True
                kw.status = "succeeded"
                kw.save(update_fields=["keywordImageUrl", "isImage", "status"])
            except Exception:
                # 실패해도 다른 키워드 진행
                kw.status = "failed"
                kw.save(update_fields=["status"])

    transaction.on_commit(_after_commit_generate)
    return trend