from typing import Tuple, List, Optional
from .models import Newsletter
from main.models import Store
from django.db.models import Q


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


def searchNewsletters(query: str = None, keyword: str = None, is_user_made: bool = None, is_liked: bool = None, page: int = None, limit: int = 9):
    """
    검색 셀렉터
    :param query: 제목/콘텐츠 검색어
    :param keyword: 키워드 이름으로 필터
    :param is_user_made: boolean으로 필터
    :param is_liked: boolean으로 필터
    :param page: 페이지 기반 페이징
    :param limit: 페이지 크기
    :return: (list[Newsletter], hasMore)
    """
    queryset = Newsletter.objects.all().select_related('store', 'user').prefetch_related('keywords').order_by('-id')

    if query:
        queryset = queryset.filter(
            Q(title__icontains=query) | Q(content__icontains=query)
        )

    if keyword:
        queryset = queryset.filter(keywords__keywordName__icontains=keyword)

    if is_user_made is not None:
        queryset = queryset.filter(isUserMade=bool(is_user_made))

    if is_liked is not None:
        queryset = queryset.filter(isLiked=bool(is_liked))

    if page is not None:
        try:
            page = int(page)
        except (ValueError, TypeError):
            raise ValueError('page 값이 유효하지 않습니다')
        if page < 1:
            raise ValueError('page 값은 1 이상의 정수여야 합니다')
        offset = (page - 1) * limit
        total = queryset.count()
        result = list(queryset[offset: offset + limit])
        hasMore = (offset + limit) < total
        return result, hasMore

    # 기본: limit 만큼 가져오고 hasMore 계산
    items = list(queryset[: limit + 1])
    hasMore = len(items) > limit
    return items[:limit], hasMore