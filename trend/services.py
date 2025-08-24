import json
from django.db import transaction
from django.conf import settings
from typing import Tuple, List
from .models import Trend, Keyword
from main.models import Store
from common.services.images import *
from common.services.trends import *


def _normalizeTrends(rawTrends: list[str]) -> list[str]:
    # 공백 제거 + 문자열화 + 순서 보존 중복 제거
    seen = set()
    normalized = []
    for t in rawTrends or []:
        s = str(t).strip()
        if not s or s in seen:
            continue
        seen.add(s)
        normalized.append(s)
    return normalized

def _pickTopKeywords(aiResp: dict | list | None, fallback: list[str], maxCount: int = 3) -> list[str]:
    if isinstance(aiResp, dict):
        if isinstance(aiResp.get("keywords"), list):
            cands = aiResp["keywords"]
        elif "keyword" in aiResp:
            cands = [aiResp["keyword"]]
        else:
            cands = []
    elif isinstance(aiResp, list):
        cands = aiResp
    else:
        cands = []

    normalized = _normalizeTrends(cands)
    if not normalized:
        normalized = _normalizeTrends(fallback)
    return normalized[:maxCount]

@transaction.atomic
def saveKeywordsFromTrends(trends: list[str], generateSync: bool = False) -> Tuple[Trend, List[Keyword]]:
    normalizedTrends = _normalizeTrends(trends)
    if not normalizedTrends:
        raise ValueError("trends 리스트가 비어있습니다.")

    trend = Trend.objects.create(trendData=json.dumps(normalizedTrends, ensure_ascii=False))

    try:
        aiResponse = extractTrends({"trends": normalizedTrends})
    except Exception:
        aiResponse = None
    keywordNames = _pickTopKeywords(aiResponse, fallback=normalizedTrends, maxCount=3)

    toCreate = [
        Keyword(
            keywordName=name,
            trend=trend,
            status="pending",
            isImage=False,
            isCreatedByUser=None,
        )
        for name in keywordNames
    ]
    createdKeywords = Keyword.objects.bulk_create(toCreate)

    if generateSync:
        
        for kw in Keyword.objects.filter(trend=trend, status="pending"):
            try:
                res = generateImageForKeyword(kw.keywordName, size="1792x1024")
                kw.keywordImageUrl = res.get("path")
                kw.isImage = True
                kw.status = "succeeded"
                kw.save(update_fields=["keywordImageUrl", "isImage", "status"])
            except Exception:
                kw.status = "failed"
                kw.save(update_fields=["status"])
    else:
        
        def _afterCommit():
            for kw in Keyword.objects.filter(trend=trend, status="pending"):
                try:
                    res = generateImageForKeyword(kw.keywordName, size="1792x1024")
                    kw.keywordImageUrl = res.get("path")
                    kw.isImage = True
                    kw.status = "succeeded"
                    kw.save(update_fields=["keywordImageUrl", "isImage", "status"])
                except Exception:
                    kw.status = "failed"
                    kw.save(update_fields=["status"])
        transaction.on_commit(_afterCommit)

    return trend, createdKeywords


def _generateImageForKeyword(keyword: Keyword):
    
    def _afterCommitGenerate():
        try:
            res = generateImageForKeyword(keyword.keywordName, size="1024x1024")
            
            keyword.keywordImageUrl = res.get("path") 
            keyword.isImage = True
            keyword.status = "succeeded"
            keyword.save(update_fields=["keywordImageUrl", "isImage", "status"])
            
        except Exception as imgError:
            print(f"Image generation failed for keyword '{keyword.keywordName}': {imgError}")
            keyword.status = "failed"
            keyword.save(update_fields=["status"])
    
    transaction.on_commit(_afterCommitGenerate)
    

def keywordSaveByUserSync(keywordName: str, store: Store) -> Keyword:
    if not keywordName or not keywordName.strip():
        raise ValueError("키워드를 입력해주세요.")
    
    keyword = Keyword.objects.create(
        keywordName=keywordName.strip(),
        trend=None,
        status="pending",
        isImage=False,
        isCreatedByUser=store
    )
    
    try:
        res = generateImageForKeyword(keyword.keywordName, size="1024x1024")
        
        keyword.keywordImageUrl = res.get("path")
        keyword.isImage = True
        keyword.status = "succeeded"
        
    except Exception as e:
        # 실패 시 상태만 실패로 표시 (프론트에서 리트라이 버튼을 두거나, 배치로 재시도 가능)
        keyword.status = "failed"
        
    finally:
        keyword.save(update_fields=["keywordImageUrl", "isImage", "status"])

    return keyword