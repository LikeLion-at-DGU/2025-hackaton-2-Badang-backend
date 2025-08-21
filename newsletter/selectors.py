from typing import Tuple, List, Optional
from .models import Newsletter
from main.models import Store


def getNewsletterList(store: Store, cursor: Optional[int] = None, limit: int = 9, page: Optional[int] = None) -> Tuple[List[Newsletter], bool]:
    """
    뉴스레터 목록을 가져오는 함수
    :param store: 스토어 아이디
    :param cursor: 다음 페이지를 위한 커서 (None이면 처음부터 시작)
    :param limit: 가져올 뉴스레터의 개수
    :param page: 페이지 기반 페이징 (page가 전달되면 cursor는 무시됨)
    :return: (뉴스레터 목록, 다음 페이지 여부)
    """
    # 최신순 정렬
    queryset = Newsletter.objects.filter(store=store).order_by('-id')

    if page is not None:
        # 페이지 기반 페이징 처리
        try:
            page = int(page)
        except (ValueError, TypeError):
            raise ValueError("page 값이 유효한 정수가 아닙니다")
        if page < 1:
            raise ValueError("page 값은 1 이상의 정수여야 합니다")

        offset = (page - 1) * limit
        total = queryset.count()
        result_qs = list(queryset[offset: offset + limit])
        hasMore = (offset + limit) < total
        return result_qs, hasMore

    # cursor 기반 페이징
    if cursor:
        try:
            cursor = int(cursor)
        except (ValueError, TypeError):
            raise ValueError("cursor 값이 유효한 정수가 아닙니다")
        queryset = queryset.filter(id__lt=cursor)

    newslettersToFetch = limit + 1
    newsletters = list(queryset[:newslettersToFetch])

    hasMore = len(newsletters) > limit
    resultNewsletters = newsletters[:limit]

    return resultNewsletters, hasMore


def getNewsletterDetail(news_id: int) -> Newsletter:

    return Newsletter.objects.select_related('store', 'user', 'review_analysis').prefetch_related('keywords').get(id=news_id)