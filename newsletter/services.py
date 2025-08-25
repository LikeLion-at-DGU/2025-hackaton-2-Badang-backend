from main.models import Store, Profile
from .models import Newsletter
from .getnewsletter import createNewsletterAI
from trend.models import Keyword
from review.models import ReviewAnalysis
from trend.serializers import KeywordRes

from django.forms.models import model_to_dict

def createNewsletter(storeId: int) -> Newsletter:
    try:
        store = Store.objects.get(pk=storeId)
        reviewAnalysis = ReviewAnalysis.objects.filter(storeId=store).first()
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
    
#사용자 키워드로 뉴스레터 제작
def createNewsletterByUser(storeId: int, keyword) -> Newsletter:
    try:
        store = Store.objects.get(pk=storeId)
        reviewAnalysis = ReviewAnalysis.objects.filter(storeId=store).first()

    except Store.DoesNotExist:
        raise ValueError("가게를 찾을 수 없습니다.")
    except ReviewAnalysis.DoesNotExist:
        raise ValueError("리뷰 분석을 찾을 수 없습니다.")
    except Keyword.DoesNotExist:
        raise ValueError("키워드를 찾을 수 없습니다.")
    
    storeData = model_to_dict(store)
    reviewData = model_to_dict(reviewAnalysis)
    keywordData = {"keyword": keyword.keywordName if hasattr(keyword, 'keywordName') else str(keyword)}

    createNewNewsletter = createNewsletterAI(reviewData, keywordData, storeData)
    user = store.user
        
    newNewsletter = Newsletter.objects.create(
        user=user,
        store=store,
        review_analysis=reviewAnalysis,
        isUserMade=True,
        title=createNewNewsletter.get("title"),
        firstContent=createNewNewsletter.get("firstContent"),
        secondContent=createNewNewsletter.get("secondContent")
    )

    try:
        if hasattr(keyword, 'pk'):
            newNewsletter.keywords.add(keyword)
        else:
            kw_obj = Keyword.objects.filter(keywordName=str(keyword)).order_by('-keywordCreatedAt').first()
            if kw_obj:
                newNewsletter.keywords.add(kw_obj)
    except Exception as e:
        print(f"Warning: could not attach keyword to newsletter: {e}")
        
    return newNewsletter