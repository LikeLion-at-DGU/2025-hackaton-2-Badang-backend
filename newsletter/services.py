from main.models import Store, Profile
from .models import Newsletter
from .getnewsletter import createNewsletterAI
from trend.models import Keyword
from review.models import ReviewAnalysis

from django.forms.models import model_to_dict

def createNewsletter(storeId: int) -> Newsletter:
    try:
        store = Store.objects.get(pk=storeId)
        reviewAnalysis = ReviewAnalysis.objects.get(storeId=store)
        keyword = Keyword.objects.latest('keywordCreatedAt') # <-- 이 부분이 중요

        if not keyword:
            raise Exception("해당 가게에 연결된 키워드가 없습니다.")  # Assuming Keyword is a model related to Store
    
    except Store.DoesNotExist:
        raise ValueError("가게를 찾을 수 없습니다.")
    except ReviewAnalysis.DoesNotExist:
        raise ValueError("리뷰 분석을 찾을 수 없습니다.")
    except Keyword.DoesNotExist:
        raise ValueError("키워드를 찾을 수 없습니다.")
    
    storeData = model_to_dict(store)
    reviewData = model_to_dict(reviewAnalysis)
    keywordData = {"keyword": keyword.keywordName}

    createNewNewsletter = createNewsletterAI(reviewData, keywordData, storeData)
    user = store.user
    newNewsletter = Newsletter.objects.create(
        user=user,
        store=store,
        review_analysis=reviewAnalysis,
        isUserMade=False,
        title=createNewNewsletter.get("title"),
        firstContent=createNewNewsletter.get("firstContent"),
        secondContent=createNewNewsletter.get("secondContent")
    )
    newNewsletter.keywords.add(keyword)
        
    return newNewsletter

def getNewsletter(newsletterId: int) -> Newsletter:
    try:
        newsletter = Newsletter.objects.get(pk=newsletterId)
        return newsletter
    
    except Newsletter.DoesNotExist:
        raise ValueError("뉴스레터를 찾을 수 없습니다.")