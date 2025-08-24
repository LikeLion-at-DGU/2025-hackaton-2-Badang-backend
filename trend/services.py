# trend/services.py
import json
from django.db import transaction
from django.conf import settings
from typing import Tuple, List
from .models import Trend, Keyword
from main.models import Store
from common.services.images import *
from common.services.trends import *

#Trend 에 저장된 걸 AI 돌려서 keyword 에 저장함
# @transaction.atomic
# def saveSingleKeywordToDB(trends: list[str]) -> Keyword:

#     # Trend DB에 저장 (JSON으로 직렬화)
#     trend = Trend.objects.create(trendData=json.dumps(trends, ensure_ascii=False))
    
#     try:
#         # AI에게 트렌드 데이터 전달
#         trendPayload = {"trends": trends}  # 또는 {"data": trends}
#         aiResponse = extractTrends(trendPayload)
        
#         extractedKeywords = []
        
#         if isinstance(aiResponse, dict):
#             # AI 응답에서 키워드 추출 (실제 응답 구조에 맞게 수정 필요)
#             if "keywords" in aiResponse and isinstance(aiResponse["keywords"], list):
#                 extractedKeywords = aiResponse["keywords"][:3]  # 최대 3개
#             elif "keyword" in aiResponse:
#                 # 단일 키워드 응답인 경우
#                 extractedKeywords = [aiResponse["keyword"]]
        
#         # AI 추출 실패 시 fallback
#         if not extractedKeywords:
#             extractedKeywords = trends[:3]
            
#     except Exception as e:
#         print(f"AI keyword extraction failed: {e}")
#         # AI 실패 시 원본 데이터에서 앞 3개 사용
#         extractedKeywords = trends[:3]
    
#     # Keyword 객체들 생성
#     kwObjs = [
#         Keyword(
#             keywordName=name.strip(),
#             trend=trend,
#             status="pending",
#             isImage=False,
#             isCreatedByUser=None,
#         )
#         for name in extractedKeywords if name and str(name).strip()
#     ]
    
#     if kwObjs:
#         Keyword.objects.bulk_create(kwObjs)
        
    
    

#     def _afterCommitGenerate():
#         for kw in Keyword.objects.filter(trend=trend, status="pending"):
#             try:
#                 res = generateImageForKeyword(kw.keywordName, size="1792x1024") 
#                 kw.keywordImageUrl = res["path"] 
#                 kw.isImage = True
#                 kw.status = "succeeded"
#                 kw.save(update_fields=["keywordImageUrl", "isImage", "status"])
#             except Exception as imgError:
#                 print(f"Image generation failed for {kw.keywordName}: {imgError}")
#                 kw.status = "failed"
#                 kw.save(update_fields=["status"])

#     transaction.on_commit(_afterCommitGenerate)
    
#     return trend


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
def saveKeywordsFromTrends(trends: list[str]) -> Tuple[Trend, List[Keyword]]:
    # 1) 입력 정제
    normalizedTrends = _normalizeTrends(trends)
    if not normalizedTrends:
        raise ValueError("trends 리스트가 비어있습니다.")

    # 2) Trend 저장
    trend = Trend.objects.create(trendData=json.dumps(normalizedTrends, ensure_ascii=False))

    # 3) AI 추출 시도 + 실패 시 fallback
    try:
        aiResponse = extractTrends({"trends": normalizedTrends})
    except Exception:
        aiResponse = None
    keywordNames = _pickTopKeywords(aiResponse, fallback=normalizedTrends, maxCount=3)

    # 4) Keyword 저장 (pending)
    toCreate = [
        Keyword(
            keywordName=name,
            trend=trend,
            status="pending",
            isImage=False,
            isCreatedByUser=None,  # FK라면 nullable OK, 네이밍은 createdByStore 권장
        )
        for name in keywordNames
    ]
    createdKeywords = Keyword.objects.bulk_create(toCreate)

    # 5) 커밋 후 이미지 생성/상태 업데이트
    def _afterCommit():
        # bulk_create는 DB에 반영됐으니 다시 조회하거나 createdKeywords를 사용해도 됨
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

    # 6) 의도에 맞게 Trend와 생성된 Keyword 리스트를 함께 반환
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

#비동기로 이미지 생성할 시!
# def keywordSaveByUserSync(keywordName: str, store: Store) -> Keyword:
#     if not keywordName or not keywordName.strip():
#         raise ValueError("키워드를 입력해주세요.")

#     keyword = Keyword.objects.create(
#         keywordName=keywordName.strip(),
#         trend=None,
#         status="pending",
#         isImage=False,
#         isCreatedByUser=store,
#     )

#     # 비동기: 커밋 후 생성 예약. 리턴 즉시에는 URL 없음
#     _generateImageForKeyword(keyword)  # ← 객체를 넘기고, size 인자 없음
#     return keyword