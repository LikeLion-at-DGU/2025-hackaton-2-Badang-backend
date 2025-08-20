from typing import Tuple, List
from .models import NewsLetter
from main.models import Store

def getNewsletterList(store: Store, cursor: int = None, limit: int = 9, ) -> Tuple[List[NewsLetter], bool]:
    """
    뉴스레터 목록을 가져오는 함수
    :param store: 스토어 아이디
    :param cursor: 다음 페이지를 위한 커서 (None이면 처음부터 시작)
    :param limit: 가져올 뉴스레터의 개수
    :return: 뉴스레터 목록과 다음 페이지 여부
    """
    queryset = NewsLetter.objects.filter(store=store)
    
    if cursor:
        queryset = queryset.filter(id__lt=cursor)

    newslettersToFetch = limit + 1
    newsletters = list(queryset[:newslettersToFetch])

    hasMore = len(newsletters) > limit
    
    resultNewsletters = newsletters[:limit]
    
    return resultNewsletters, hasMore