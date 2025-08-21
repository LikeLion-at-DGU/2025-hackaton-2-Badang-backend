import requests, environ, json
from datetime import timedelta
from django.utils import timezone
from .models import Review, Reviewer, ReviewAnalysis
from main.models import Store
from .reviewAnalisys import review_analysis
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
    
    query = f"{storeName} {storeAddress}"
    params = {"query": query}
    
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if data.get("documents"):
        first_document = data["documents"][0]
        
        return {
            "id": first_document["id"],
            "placePhone": first_document["phone"],
            "placeLatitude": first_document["y"],
            "placeLongitude": first_document["x"],
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
    try:
        store = Store.objects.get(pk=storeId)
        # Store 모델에 카카오맵 ID를 저장하는 필드가 'kakao_place_id'라고 가정
        if not store.kakaoPlaceId:
            raise ValueError("가게에 kakaoPlaceId가 등록되어 있지 않습니다.")
    except (Store.DoesNotExist, ValueError) as e:
        print(f"서비스 처리 불가: {e}")
        return None # 가게가 없거나 kakao_id가 없으면 None 반환

    # 최신 리뷰를 위해 크롤러 실행 및 DB 업데이트
    # (주의: API 호출마다 크롤링이 실행되어 느릴 수 있음. 캐싱 전략 고려 필요)
    scrapedReviews = getKakaoReview(store.kakaoPlaceId)
    if scrapedReviews:
        updateReviewData(store, scrapedReviews)

    # 'term' 값에 따라 리뷰 필터링
    endDate = timezone.now()
    reviews_qs = store.reviews.all()
    
    if term == 1: # 한 달
        startDate = endDate - timedelta(days=30)
        reviews_qs = reviews_qs.filter(reviewDate__range=[startDate, endDate])
    elif term == 2: # 일주일
        startDate = endDate - timedelta(days=7)
        reviews_qs = reviews_qs.filter(reviewDate__range=[startDate, endDate])
    
    if not reviews_qs.exists():
        return {"message": "해당 기간에 분석할 리뷰가 없습니다."}

    # 필터링된 리뷰로 LLM 페이로드 생성 (버그 수정)
    review_payload = [
        {
            "reviewContent": r.reviewContent,
            "reviewRate": r.reviewRate,
            "reviewDate": r.reviewDate.strftime("%Y-%m-%d"),
        } for r in reviews_qs
    ]
    payload = {"storeName": store.name, "reviews": review_payload}

    # LLM 분석 실행
    try:
        analysisResult = review_analysis(payload) 
        
        # 'analysisKeyword'가 '리뷰 분석 실패'와 같은 기본값인지 확인하여
        # 성공 여부를 판단하고 DB에 저장
        is_success = analysisResult.get('analysisKeyword') != '리뷰 분석 실패'

        if is_success:
            # get() 메서드를 사용하여 안전하게 키에 접근
            percentage_data = analysisResult.get('percentage', {})
            
            # 성공 시에만 DB에 저장하는 로직 실행
            review_analysis_obj, created = ReviewAnalysis.objects.get_or_create(
                storeId=store,
                defaults={
                    'analysisKeyword': analysisResult.get('analysisKeyword', '분석 실패'),
                    'goodPoint': analysisResult.get('goodPoint', '분석 실패'),
                    'badPoint': analysisResult.get('badPoint', '분석 실패'),
                    'goodPercentage': percentage_data.get('goodPercentage', 0),
                    'badPercentage': percentage_data.get('badPercentage', 0),
                    'middlePercentage': percentage_data.get('middlePercentage', 0),
                }
            )

            if not created:
                # 이미 객체가 있다면 .get()을 사용하여 업데이트
                review_analysis_obj.analysisKeyword = analysisResult.get('analysisKeyword', '분석 실패')
                review_analysis_obj.goodPoint = analysisResult.get('goodPoint', '분석 실패')
                review_analysis_obj.badPoint = analysisResult.get('badPoint', '분석 실패')
                review_analysis_obj.goodPercentage = percentage_data.get('goodPercentage', 0)
                review_analysis_obj.badPercentage = percentage_data.get('badPercentage', 0)
                review_analysis_obj.middlePercentage = percentage_data.get('middlePercentage', 0)
                review_analysis_obj.save()

            return {"message": "리뷰 분석 및 저장 성공", "data": analysisResult}
        else:
            # 분석에 실패한 경우
            return {"message": "리뷰 분석 중 오류가 발생했습니다. LLM 응답 형식에 문제가 있습니다.", "data": analysisResult}

    except Exception as e:
        print(f"리뷰 분석 실패: {e}")
        return {"message": "리뷰 분석 중 오류가 발생했습니다.", "error": str(e)}