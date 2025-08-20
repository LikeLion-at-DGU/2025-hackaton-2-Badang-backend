# trend/services.py
import json
from django.db import transaction
from django.conf import settings
from .models import Trend, Keyword
from main.models import Store
from common.services.images import *
from common.services.trends import *

#Trend 에 저장된 걸 AI 돌려서 keyword 에 저장함
@transaction.atomic
def saveSingleKeywordToDB(trends: list[str]) -> Keyword:

    # Trend DB에 저장 (JSON으로 직렬화)
    trend = Trend.objects.create(trendData=json.dumps(trends, ensure_ascii=False))
    
    try:
        # AI에게 트렌드 데이터 전달
        trendPayload = {"trends": trends}  # 또는 {"data": trends}
        aiResponse = extractTrends(trendPayload)
        
        extractedKeywords = []
        
        if isinstance(aiResponse, dict):
            # AI 응답에서 키워드 추출 (실제 응답 구조에 맞게 수정 필요)
            if "keywords" in aiResponse and isinstance(aiResponse["keywords"], list):
                extractedKeywords = aiResponse["keywords"][:3]  # 최대 3개
            elif "keyword" in aiResponse:
                # 단일 키워드 응답인 경우
                extractedKeywords = [aiResponse["keyword"]]
        
        # AI 추출 실패 시 fallback
        if not extractedKeywords:
            extractedKeywords = trends[:3]
            
    except Exception as e:
        print(f"AI keyword extraction failed: {e}")
        # AI 실패 시 원본 데이터에서 앞 3개 사용
        extractedKeywords = trends[:3]
    
    # Keyword 객체들 생성
    kwObjs = [
        Keyword(
            keywordName=name.strip(),
            trend=trend,
            status="pending",
            isImage=False,
            isCreatedByUser=None,
        )
        for name in extractedKeywords if name and str(name).strip()
    ]
    
    if kwObjs:
        Keyword.objects.bulk_create(kwObjs)
        
    
    

    def _afterCommitGenerate():
        for kw in Keyword.objects.filter(trend=trend, status="pending"):
            try:
                relPath = generateLocalImageForKeyword(kw.keywordName, size="512x512")
                url = settings.MEDIA_URL.rstrip("/") + "/" + relPath.lstrip("/")
                kw.keywordImageUrl = url
                kw.isImage = True
                kw.status = "succeeded"
                kw.save(update_fields=["keywordImageUrl", "isImage", "status"])
            except Exception as imgError:
                print(f"Image generation failed for {kw.keywordName}: {imgError}")
                kw.status = "failed"
                kw.save(update_fields=["status"])

    transaction.on_commit(_afterCommitGenerate)
    
    return trend

@transaction.atomic
def keywordSaveByUserSimple(keywordName: str = "", store: Store = None) -> Keyword:

    if not keywordName or not keywordName.strip():
        raise ValueError("키워드를 입력해주세요.")
    
    # Keyword 객체 생성
    keyword = Keyword.objects.create(
        keywordName=keywordName.strip(),
        trend=None,
        status="pending",
        isImage=False,
        isCreatedByUser=store 
    )
    
    # 공통 이미지 생성 함수 호출
    _generateImageForKeyword(keyword)
    
    return keyword

def _generateImageForKeyword(keyword: Keyword):
    
    def _afterCommitGenerate():
        try:
            relPath = generateLocalImageForKeyword(keyword.keywordName, size="1024x1024")
            url = settings.MEDIA_URL.rstrip("/") + "/" + relPath.lstrip("/")
            keyword.keywordImageUrl = url
            keyword.isImage = True
            keyword.status = "succeeded"
            keyword.save(update_fields=["keywordImageUrl", "isImage", "status"])
        except Exception as imgError:
            print(f"Image generation failed for keyword '{keyword.keywordName}': {imgError}")
            keyword.status = "failed"
            keyword.save(update_fields=["status"])
    
    transaction.on_commit(_afterCommitGenerate)