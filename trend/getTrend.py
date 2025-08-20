# 구글 정책 상 pytrend 를 이용한 크롤링이 막힘 -> 별도의 DB 제작해서 진행
# from typing import List
# from pytrends.request import TrendReq

# def get_seed_keywords(geo: str = "KR", limit: int = 100) -> List[str]:
#     pytrends = TrendReq(hl='ko' if geo.upper() == 'KR' else 'en-US',
#                         tz=540 if geo.upper() == 'KR' else 0)
#     seeds: list[str] = []

#     # 실시간 급상승
#     try:
#         rt = pytrends.realtime_trending_searches(pn='KR' if geo.upper() == 'KR' else 'US')
#         if rt is not None and 'title' in rt:
#             seeds += rt['title'].dropna().astype(str).tolist()
#     except Exception:
#         pass

#     # 오늘의 급상승
#     try:
#         daily = pytrends.trending_searches(pn='south_korea' if geo.upper() == 'KR' else 'united_states')
#         if daily is not None and 0 in daily:
#             seeds += daily[0].dropna().astype(str).tolist()
#     except Exception:
#         pass

#     # 정제
#     cleaned = [s.strip() for s in seeds if isinstance(s, str) and s.strip()]
#     deduped = list(dict.fromkeys(cleaned))

#     # 폴백: 그래도 비면 최소한의 기본 시드 사용
#     if not deduped:
#         deduped = ["올림픽", "아이유", "카카오뱅크", "이강인", "부산 여행", "디즈니 플러스"]

#     return deduped[:limit]
