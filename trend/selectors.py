from newsletter.models import Newsletter

def getNewsletterDetail(news_id: int) -> Newsletter:

    return Newsletter.objects.select_related('store', 'user', 'review_analysis').prefetch_related('keywords').get(id=news_id)