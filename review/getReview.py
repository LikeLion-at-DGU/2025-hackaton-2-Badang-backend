import time
from datetime import datetime
from typing import List, Dict, Any

from selenium import webdriver
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup


def _buildChromeOptions() -> webdriver.ChromeOptions:
    opts = webdriver.ChromeOptions()
    # 헤드리스 신규 엔진 + 서버 안정화 옵션
    opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1280,800")
    # UA 지정(봇 차단 회피용이 아니라 안정적 렌더링용)
    opts.add_argument(
        "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/125.0.0.0 Safari/537.36"
    )
    # 불필요한 확장 비활성화
    opts.add_experimental_option("excludeSwitches", ["enable-automation"])
    opts.add_experimental_option("useAutomationExtension", False)
    return opts


def _parseKakaoDate(raw: str) -> datetime:
    """
    카카오맵 리뷰 날짜 포맷이 '2025.08.20.' or '어제', '방금 전' 등으로 섞일 수 있어
    가장 흔한 케이스만 우선 처리하고, 실패 시 now 반환.
    """
    if not raw:
        return datetime.now()
    raw = raw.strip()
    try:
        # 기본 포맷: 2025.08.20.
        return datetime.strptime(raw, "%Y.%m.%d.")
    except Exception:
        # 간단한 휴리스틱
        if "방금" in raw:
            return datetime.now()
        if "분 전" in raw:
            return datetime.now()
        if "시간 전" in raw:
            return datetime.now()
        if "어제" in raw:
            return datetime.now()
        return datetime.now()


def getKakaoReview(kakaoPlaceId: str, maxCount: int = 50) -> List[Dict[str, Any]]:
    """
    카카오맵 place 페이지(https://place.map.kakao.com/{id})에서 리뷰 스크래핑.
    반환: [{"reviewerName": "...", "content": "...", "rate": 5, "date": datetime}, ...]
    """
    url = f"https://place.map.kakao.com/{kakaoPlaceId}"
    options = _buildChromeOptions()
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)

    scrapedReviews: List[Dict[str, Any]] = []

    try:
        driver.set_page_load_timeout(25)
        driver.get(url)

        wait = WebDriverWait(driver, 20)

        # ★ 카카오 place는 종종 iframe으로 실제 내용이 뜸 (entryIframe 또는 webapp 내부 프레임)
        try:
            iframe = wait.until(
                EC.presence_of_element_located(
                    (By.CSS_SELECTOR, "iframe#entryIframe, iframe#kakaoWrap iframe")
                )
            )
            driver.switch_to.frame(iframe)
        except TimeoutException:
            # 프레임이 없는 구조일 수도 있으니 패스
            pass

        # '후기' 탭이 클릭 가능한 상태까지 대기 후 클릭
        # (텍스트 기반 XPATH는 변경에 취약 → data-tab 혹은 role 기반으로 먼저 시도, 안 되면 텍스트 폴백)
        try:
            reviewTab = wait.until(
                EC.element_to_be_clickable(
                    (By.CSS_SELECTOR, "a[role='tab'][href*='review'], a[aria-controls*='review']")
                )
            )
        except TimeoutException:
            reviewTab = wait.until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(., '후기')]"))
            )

        driver.execute_script("arguments[0].click();", reviewTab)

        # 리뷰 리스트 컨테이너 대기
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.list_review")))

        # 무한 스크롤/더보기 처리
        # 1) 스크롤로 로드 시도
        # 2) 멈추면 '더보기' 버튼 클릭 시도
        loadedCount = 0
        sameCountHit = 0
        while True:
            # 현재까지 파싱해 본 개수
            html = driver.page_source
            soup = BeautifulSoup(html, "html.parser")
            items = soup.select("ul.list_review > li")
            if len(items) > loadedCount:
                loadedCount = len(items)
                sameCountHit = 0
            else:
                sameCountHit += 1

            if loadedCount >= maxCount:
                break

            # 스크롤 다운
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.2)

            # '더보기' 버튼 폴백
            if sameCountHit >= 2:  # 두 번 연속 늘지 않으면 더보기 시도
                try:
                    moreBtn = driver.find_element(By.CSS_SELECTOR, "a.link_more, button.link_more")
                    driver.execute_script("arguments[0].click();", moreBtn)
                    time.sleep(1.2)
                    sameCountHit = 0
                except NoSuchElementException:
                    break

        # 최종 파싱
        html = driver.page_source
        soup = BeautifulSoup(html, "html.parser")
        reviewList = soup.select("ul.list_review > li")

        for li in reviewList[:maxCount]:
            reviewerName = (
                li.select_one("span.name_user").get_text(strip=True)
                if li.select_one("span.name_user")
                else "익명"
            )
            content = (
                li.select_one("p.desc_review").get_text(strip=True)
                if li.select_one("p.desc_review")
                else ""
            )

            # 별점: 'on' 클래스 개수로 계산 (DOM 변화 시 조정 필요)
            starOn = li.select(".ico_star.on")
            rate = len(starOn) if starOn else 0

            dateStr = (
                li.select_one(".txt_date").get_text(strip=True)
                if li.select_one(".txt_date")
                else None
            )
            reviewDate = _parseKakaoDate(dateStr)

            scrapedReviews.append(
                {
                    "reviewerName": reviewerName,
                    "content": content,
                    "rate": rate,
                    "date": reviewDate,
                }
            )

        return scrapedReviews

    finally:
        driver.quit()



# import time
# from datetime import datetime
# from selenium import webdriver
# from selenium.common.exceptions import TimeoutException
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from bs4 import BeautifulSoup

# def getKakaoReview(kakaoPlaceId: str) -> list:
#     """
#     주어진 카카오맵 ID의 리뷰를 스크래핑하여 딕셔너리 리스트로 반환합니다.
#     [{"reviewer_name": "...", "content": "...", "rate": 5, "date": "2025.08.20."}, ...]
#     """
#     url = f"https://place.map.kakao.com/{kakaoPlaceId}"
    
#     options = webdriver.ChromeOptions()
#     options.add_argument("headless")
#     options.add_argument("window-size=1920x1080")
#     options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=options)
    
#     scraped_reviews = []

#     try:
#         print(f"  [Scraper] 페이지 접속: {url}")
#         driver.get(url)

#         review_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., '후기')]")))
#         driver.execute_script("arguments[0].click();", review_tab)
        
#         WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.list_review")))

#         last_height = driver.execute_script("return document.body.scrollHeight")
#         while True:
#             driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#             time.sleep(1.5)
#             new_height = driver.execute_script("return document.body.scrollHeight")
#             if new_height == last_height:
#                 try:
#                     more_button = driver.find_element(By.CSS_SELECTOR, "a.link_more")
#                     driver.execute_script("arguments[0].click();", more_button)
#                     time.sleep(1.5)
#                 except:
#                     break
#             last_height = new_height
        
#         html = driver.page_source
#         soup = BeautifulSoup(html, 'html.parser')
#         review_list = soup.select('ul.list_review > li')

#         print(f"  [Scraper] {len(review_list)}개의 리뷰 아이템 발견.")
#         for item in review_list:
#             reviewerName = item.select_one('span.name_user').get_text(strip=True) if item.select_one('span.name_user') else "익명"
#             content = item.select_one('p.desc_review').get_text(strip=True) if item.select_one('p.desc_review') else ""
            
#             # 별점 추출 (별의 개수로 계산)
#             rate = len(item.select('.ico_star.on')) if item.select('.ico_star.on') else 0
            
#             # 날짜 추출 및 변환
#             date_str = item.select_one('.txt_date').get_text(strip=True) if item.select_one('.txt_date') else None
#             review_date = datetime.strptime(date_str, '%Y.%m.%d.') if date_str else datetime.now()

#             scraped_reviews.append({
#                 'reviewerName': reviewerName,
#                 'content': content,
#                 'rate': rate,
#                 'date': review_date,
#             })
            
#     except Exception as e:
#         print(f"  [Scraper] 크롤링 중 에러 발생: {e}")
#     finally:
#         driver.quit()
        
#     return scraped_reviews