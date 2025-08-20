from main.models import Store, Profile
from .models import Newsletter
from .getnewsletter import createNewsletterAI
from trend.models import Keyword
from review.models import ReviewAnalysis

from django import Request
from django.forms.models import model_to_dict

def createNewsletter(storeId: int) -> Newsletter:
    try:
        store = Store.objects.get(pk=storeId)
        reviewAnalysis = ReviewAnalysis.objects.get(store=store)
        keyword = Keyword.objects.filter(store=store).first()  # Assuming Keyword is a model related to Store
    
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

    newNewsletter = Newsletter.objects.create(
        store=store,
        reviewAnalysis=reviewAnalysis,
        keyword=keyword,
        title=createNewNewsletter.get("title"),
        content=createNewNewsletter.get("content")
    )

    return newNewsletter

def getNewsletter(newsletterId: int) -> Newsletter:
    try:
        newsletter = Newsletter.objects.get(pk=newsletterId)
        return newsletter
    
    except Newsletter.DoesNotExist:
        raise ValueError("뉴스레터를 찾을 수 없습니다.")