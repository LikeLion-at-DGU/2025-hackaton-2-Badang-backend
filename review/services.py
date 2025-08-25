import requests, environ, json
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .models import Review, Reviewer, ReviewAnalysis
from main.models import Store
from .reviewAnalisys import reviewAnalysisByAI
from common.services.llm import run_llm
from .getReview import getKakaoReview
import logging

env = environ.Env()
logger = logging.getLogger(__name__)
    
def getStoreId(storeName, storeAddress):
    KAKAO_KEY = env.get_value("KAKAO_KEY")
    api_key = KAKAO_KEY
    url = "https://dapi.kakao.com/v2/local/search/keyword.json"
    
    headers = {
        "Authorization": f"KakaoAK {api_key}"
    }

    # 키워드와 주소를 함께 넣어 검색 정확도를 높입니다.
    query = f"{storeName} {storeAddress}"
    params = {"query": query}
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if not data.get("documents"):
        # 검색 결과가 없으면 예외 발생
        print(f"매장 정보를 찾을 수 없습니다: {query}")
        return None # 또는 예외를 발생시킵니다.

    firstDocument = data["documents"][0]
    
    return {
        "id": firstDocument.get("id"),
        "placePhone": firstDocument.get("phone"),
        "placeLatitude": firstDocument.get("y"),
        "placeLongitude": firstDocument.get("x"),
    }

def updateReviewData(store: Store, reviewData: list):
    """리뷰 데이터를 DB에 저장"""
    if not reviewData:
        print(f"[updateReviewData] No review data to update for store {store.id}")
        logger.info(f"No review data to update for store {store.id}")
        return
    
    createReview = []
    
    print(f"[updateReviewData] Processing {len(reviewData)} reviews for store {store.id}")
    logger.info(f"Processing {len(reviewData)} reviews for store {store.id}")
    
    for data in reviewData:
        try:
            reviewer, created = Reviewer.objects.get_or_create(
                reviewerName=data.get('reviewerName', '익명'),
                defaults={
                    'follower': data.get("follower", 0),
                    'reviewCount': data.get("reviewCount", 0),
                    'reviewAvg': data.get("reviewAvg", 0.0),
                }
            )
            
            createReview.append(
                Review(
                    storeId=store,
                    reviewer=reviewer,
                    reviewContent=data.get('content', ''),
                    reviewDate=data.get('date', timezone.now()),
                    reviewRate=data.get('rate', 0)
                )
            )
        except Exception as e:
            print(f"[updateReviewData] Error processing review data: {e}")
            logger.error(f"Error processing review data: {e}")
            continue
    
    if createReview:
        try:
            Review.objects.bulk_create(createReview, ignore_conflicts=True)
            print(f"[updateReviewData] Successfully created {len(createReview)} reviews")
            logger.info(f"Successfully created {len(createReview)} reviews")
        except Exception as e:
            print(f"[updateReviewData] Error bulk creating reviews: {e}")
            logger.error(f"Error bulk creating reviews: {e}")
    else:
        print("[updateReviewData] No valid reviews to create")
        logger.warning("No valid reviews to create")

def postReviewAnalysis(storeId: int, term: int):
    """
    리뷰 분석을 실행하는 메인 함수
    Args:
        storeId (int): 분석할 스토어 ID
        term (int): 분석 기간 (0: 전체, 1: 한달, 2: 일주일)
    Returns:
        dict: 분석 결과 또는 에러 메시지
    """
    print(f"[postReviewAnalysis] Starting analysis - storeId: {storeId}, term: {term}")
    logger.info(f"Starting review analysis - storeId: {storeId}, term: {term}")
    
    try:
        # 1. 스토어 조회 및 검증
        store = Store.objects.get(pk=storeId)
        print(f"[postReviewAnalysis] Store found: {store.name}")
        logger.info(f"Store found: {store.name}, kakaoPlaceId: {store.kakaoPlaceId}")
        
        if not store.kakaoPlaceId:
            error_msg = f"Store {storeId} has no kakaoPlaceId"
            print(f"[postReviewAnalysis] {error_msg}")
            logger.error(error_msg)
            return {"message": "가게에 kakaoPlaceId가 등록되어 있지 않습니다.", "error": "NO_KAKAO_PLACE_ID"}
            
    except Store.DoesNotExist as e:
        error_msg = f"Store {storeId} does not exist"
        print(f"[postReviewAnalysis] {error_msg}")
        logger.error(error_msg)
        return {"message": "존재하지 않는 가게입니다.", "error": "STORE_NOT_FOUND"}
    except Exception as e:
        error_msg = f"Unexpected error while fetching store: {e}"
        print(f"[postReviewAnalysis] {error_msg}")
        logger.error(error_msg)
        return {"message": "스토어 조회 중 오류가 발생했습니다.", "error": str(e)}

    # 2. 카카오 리뷰 크롤링
    try:
        print(f"[postReviewAnalysis] Calling getKakaoReview with kakaoPlaceId: {store.kakaoPlaceId}")
        logger.info(f"Calling getKakaoReview with kakaoPlaceId: {store.kakaoPlaceId}")
        
        scrapedReviews = getKakaoReview(store.kakaoPlaceId)
        scraped_count = len(scrapedReviews) if scrapedReviews else 0
        
        print(f"[postReviewAnalysis] Scraped {scraped_count} reviews")
        logger.info(f"Scraped {scraped_count} reviews")
        
        if scrapedReviews:
            updateReviewData(store, scrapedReviews)
        else:
            print("[postReviewAnalysis] No reviews scraped from Kakao")
            logger.warning("No reviews scraped from Kakao")
            
    except Exception as e:
        error_msg = f"Error during review scraping: {e}"
        print(f"[postReviewAnalysis] {error_msg}")
        logger.error(error_msg)
        # 크롤링 실패해도 기존 DB 리뷰로 분석 계속 진행

    # 3. 리뷰 필터링
    try:
        date = timezone.now()
        reviewsQuerySet = store.reviews.all()
        total_reviews = reviewsQuerySet.count()
        
        print(f"[postReviewAnalysis] Total reviews in store: {total_reviews}")
        logger.info(f"Total reviews in store: {total_reviews}")
        
        if term == 1:  # 한 달
            reviewsQuerySet = reviewsQuerySet.filter(reviewDate__gte=date - timedelta(days=30))
            filtered_count = reviewsQuerySet.count()
            print(f"[postReviewAnalysis] Reviews in last 30 days: {filtered_count}")
            logger.info(f"Reviews in last 30 days: {filtered_count}")
            
        elif term == 2:  # 일주일
            reviewsQuerySet = reviewsQuerySet.filter(reviewDate__gte=date - timedelta(days=7))
            filtered_count = reviewsQuerySet.count()
            print(f"[postReviewAnalysis] Reviews in last 7 days: {filtered_count}")
            logger.info(f"Reviews in last 7 days: {filtered_count}")
        else:
            filtered_count = total_reviews
            print(f"[postReviewAnalysis] Using all reviews (term=0): {filtered_count}")
            logger.info(f"Using all reviews (term=0): {filtered_count}")

        if not reviewsQuerySet.exists():
            warning_msg = f"No reviews found for term {term}"
            print(f"[postReviewAnalysis] {warning_msg}")
            logger.warning(warning_msg)
            return {"message": "해당 기간에 분석할 리뷰가 없습니다.", "error": "NO_REVIEWS_FOR_TERM"}

    except Exception as e:
        error_msg = f"Error during review filtering: {e}"
        print(f"[postReviewAnalysis] {error_msg}")
        logger.error(error_msg)
        return {"message": "리뷰 필터링 중 오류가 발생했습니다.", "error": str(e)}

    # 4. LLM 페이로드 생성
    try:
        reviewPayload = [
            {
                "reviewContent": review.reviewContent,
                "reviewRate": review.reviewRate,
                "reviewDate": review.reviewDate.strftime("%Y-%m-%d"),
            } for review in reviewsQuerySet
        ]
        payload = {"storeName": store.name, "reviews": reviewPayload}
        
        print(f"[postReviewAnalysis] Created payload with {len(reviewPayload)} reviews")
        logger.info(f"Created payload with {len(reviewPayload)} reviews")
        
    except Exception as e:
        error_msg = f"Error creating LLM payload: {e}"
        print(f"[postReviewAnalysis] {error_msg}")
        logger.error(error_msg)
        return {"message": "분석 데이터 생성 중 오류가 발생했습니다.", "error": str(e)}

    # 5. LLM 분석 실행
    try:
        print(f"[postReviewAnalysis] Starting LLM analysis...")
        logger.info(f"Starting LLM analysis with {len(reviewPayload)} reviews")
        
        analysisResult = reviewAnalysisByAI(payload)
        
        if not analysisResult:
            error_msg = "LLM analysis returned None"
            print(f"[postReviewAnalysis] {error_msg}")
            logger.error(error_msg)
            return {"message": "리뷰 분석 결과를 받을 수 없습니다.", "error": "LLM_ANALYSIS_FAILED"}
        
        print(f"[postReviewAnalysis] LLM analysis completed")
        logger.info(f"LLM analysis result keys: {analysisResult.keys() if analysisResult else 'None'}")

        # 분석 성공 여부 확인
        isSuccess = analysisResult.get('analysisKeyword') != '리뷰 분석 실패'
        print(f"[postReviewAnalysis] Analysis success: {isSuccess}")
        logger.info(f"Analysis success: {isSuccess}")

        if isSuccess:
            # 6. DB 저장
            try:
                percentageData = analysisResult.get('percentage', {})

                reviewAnalysisResult, created = ReviewAnalysis.objects.update_or_create(
                    storeId=store,
                    term=term,
                    defaults={
                        'storeName': store.name,
                        'goodPoint': analysisResult.get('goodPoint', '분석 실패'),
                        'badPoint': analysisResult.get('badPoint', '분석 실패'),
                        'goodPercentage': percentageData.get('goodPercentage', 0),
                        'badPercentage': percentageData.get('badPercentage', 0),
                        'middlePercentage': percentageData.get('middlePercentage', 0),
                        'analysisKeyword': analysisResult.get('analysisKeyword', '분석 실패'),
                        'analysisProblem': analysisResult.get('analysisProblem', '분석 실패'),
                        'analysisSolution': analysisResult.get("analysisSolution", "분석 실패"),
                    }
                )
                
                print(f"[postReviewAnalysis] ReviewAnalysis saved successfully. Created: {created}, ID: {reviewAnalysisResult.reviewAnalysisId}")
                logger.info(f"ReviewAnalysis saved successfully. Created: {created}, ID: {reviewAnalysisResult.reviewAnalysisId}")
                
                return {"message": "리뷰 분석 및 저장 성공", "data": analysisResult, "success": True}
                
            except Exception as e:
                error_msg = f"Error saving analysis result: {e}"
                print(f"[postReviewAnalysis] {error_msg}")
                logger.error(error_msg)
                return {"message": "분석 결과 저장 중 오류가 발생했습니다.", "error": str(e)}
        
        else:
            # 분석에 실패한 경우
            error_msg = f"LLM analysis failed - analysisKeyword: {analysisResult.get('analysisKeyword')}"
            print(f"[postReviewAnalysis] {error_msg}")
            logger.error(error_msg)
            return {"message": "리뷰 분석 중 오류가 발생했습니다. LLM 응답 형식에 문제가 있습니다.", "data": analysisResult, "success": False}

    except Exception as e:
        error_msg = f"Error during LLM analysis: {e}"
        print(f"[postReviewAnalysis] {error_msg}")
        logger.error(error_msg)
        return {"message": "리뷰 분석 중 오류가 발생했습니다.", "error": str(e)}