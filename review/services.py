import requests, environ, json
from datetime import timedelta
from django.core.exceptions import ObjectDoesNotExist
from django.utils import timezone
from .models import Review, Reviewer, ReviewAnalysis
from main.models import Store
from .reviewAnalisys import reviewAnalysisByAI
from common.services.llm import run_llm
from .getReview import getKakaoReview
env = environ.Env()
    
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
    createReview = []
    
    for data in reviewData:
        reviewer, _ = Reviewer.objects.get_or_create(
            follower=data.get("follower", 0),
            reviewCount=data.get("reviewCount", 0),
            reviewAvg=data.get("reviewAvg", 0.0),
            reviewerName=data['reviewerName']
        )
        createReview.append(
            Review(
                storeId=store,
                reviewer=reviewer,
                reviewContent=data['content'],
                reviewDate=data['date'],
                reviewRate=data['rate']
            )
        )
    Review.objects.bulk_create(createReview)

def postReviewAnalysis(storeId: int, term: int):
    print("리뷰 분석 시작")
    try:
        store = Store.objects.get(pk=storeId)
        if not store.kakaoPlaceId:
            raise ValueError("가게에 kakaoPlaceId가 등록되어 있지 않습니다.")
    except (Store.DoesNotExist, ValueError) as e:
        print(f"서비스 처리 불가: {e}")
        return None # 가게가 없거나 kakao_id가 없으면 None 반환

    scrapedReviews = getKakaoReview(store.kakaoPlaceId)
    if scrapedReviews:
        updateReviewData(store, scrapedReviews)

    print("리뷰 데이터:", scrapedReviews)
    
    # term에 따라 리뷰 필터링
    date = timezone.now()
    reviewsQuerySet = store.reviews.all()
    
    if term == 1: # 한 달
        reviewsQuerySet = reviewsQuerySet.filter(reviewDate__gte=date - timedelta(days=30))

    elif term == 2: # 일주일, 유저 결제 여부 판별 필요?
        reviewsQuerySet = reviewsQuerySet.filter(reviewDate__gte=date - timedelta(days=7))

    if not reviewsQuerySet.exists():
        return {"message": "해당 기간에 분석할 리뷰가 없습니다."}

    # 필터링된 리뷰로 LLM 페이로드 생성 
    reviewPayload = [
        {
            "reviewContent": review.reviewContent,
            "reviewRate": review.reviewRate,
            "reviewDate": review.reviewDate.strftime("%Y-%m-%d"),
        } for review in reviewsQuerySet
    ]
    payload = {"storeName": store.name, "reviews": reviewPayload}

    # LLM 분석 실행
    try:
        analysisResult = reviewAnalysisByAI(payload)

        # 'analysisKeyword'가 '리뷰 분석 실패'와 같은 기본값인지 확인하여
        # 성공 여부를 판단하고 DB에 저장
        isSuccess = analysisResult.get('analysisKeyword') != '리뷰 분석 실패'

        if isSuccess:
            # get() 메서드를 사용하여 안전하게 키에 접근
            percentageData = analysisResult.get('percentage', {})

            # 성공 시에만 DB에 저장하는 로직 실행
            reviewAnalysisResult, created = ReviewAnalysis.objects.update_or_create(
                storeId=store,
                term=term,  # term을 조건에 포함
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

            return {"message": "리뷰 분석 및 저장 성공", "data": analysisResult}
        
        else:
            # 분석에 실패한 경우
            return {"message": "리뷰 분석 중 오류가 발생했습니다. LLM 응답 형식에 문제가 있습니다.", "data": analysisResult}

    except Exception as e:
        print(f"리뷰 분석 실패: {e}")
        return {"message": "리뷰 분석 중 오류가 발생했습니다.", "error": str(e)}