# import time, tempfile, shutil
# from datetime import datetime
# from typing import List, Dict, Any

# from selenium import webdriver
# from selenium.common.exceptions import TimeoutException, NoSuchElementException
# from selenium.webdriver.common.by import By
# from selenium.webdriver.support.ui import WebDriverWait
# from selenium.webdriver.support import expected_conditions as EC
# from selenium.webdriver.chrome.service import Service
# from webdriver_manager.chrome import ChromeDriverManager
# from bs4 import BeautifulSoup


# def _buildChromeOptions() -> webdriver.ChromeOptions:
#     opts = webdriver.ChromeOptions()
#     opts.add_argument("--headless=new")
#     opts.add_argument("--no-sandbox")
#     opts.add_argument("--disable-dev-shm-usage")
#     opts.add_argument("--disable-gpu")
#     opts.add_argument("--window-size=1280,800")
#     opts.add_argument("--remote-debugging-port=0")  # 포트 자동 할당(충돌 방지)
#     # DOM 전부 기다리지 않고 DOMContentLoaded 수준에서 진행 → 전체 시간 단축
#     opts.page_load_strategy = "eager"
#     # 선택: UA 고정이 필요하면 유지
#     opts.add_argument(
#         "--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
#         "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
#     )
#     # 자동화 플래그 감추기(안정화 목적)
#     opts.add_experimental_option("excludeSwitches", ["enable-automation"])
#     opts.add_experimental_option("useAutomationExtension", False)
#     return opts


# def _parseKakaoDate(raw: str) -> datetime:
#     if not raw:
#         return datetime.now()
#     raw = raw.strip()
#     try:
#         return datetime.strptime(raw, "%Y.%m.%d.")
#     except Exception:
#         return datetime.now()


# def getKakaoReview(kakaoPlaceId: str, maxCount: int = 20) -> List[Dict[str, Any]]:
#     """
#     카카오맵 place 페이지에서 리뷰 스크래핑.
#     반환: [{"reviewerName": str, "content": str, "rate": int, "date": datetime}, ...]
#     """
#     url = f"https://place.map.kakao.com/{kakaoPlaceId}"

#     # 실행 시간 상한 & 스크롤 상한
#     startAt = time.monotonic()
#     timeBudget = 25.0       # 함수 전체 25초 이내로 컷
#     scrollLimit = 15        # 최대 스크롤 시도

#     # 요청마다 고유 프로필/캐시 디렉터리(동시 실행 충돌 방지)
#     tmpDir = tempfile.mkdtemp(prefix="chrome-")
#     options = _buildChromeOptions()
#     options.add_argument(f"--user-data-dir={tmpDir}")
#     options.add_argument(f"--disk-cache-dir={tmpDir}/cache")

#     service = Service(ChromeDriverManager().install())
#     driver = webdriver.Chrome(service=service, options=options)

#     scrapedReviews: List[Dict[str, Any]] = []

#     try:
#         driver.set_page_load_timeout(20)
#         driver.get(url)

#         wait = WebDriverWait(driver, 20)

#         # 종종 iframe에 실제 콘텐츠가 있음
#         try:
#             iframe = wait.until(
#                 EC.presence_of_element_located(
#                     (By.CSS_SELECTOR, "iframe#entryIframe, iframe#kakaoWrap iframe")
#                 )
#             )
#             driver.switch_to.frame(iframe)
#         except TimeoutException:
#             pass

#         # 후기 탭 클릭
#         try:
#             reviewTab = wait.until(
#                 EC.element_to_be_clickable(
#                     (By.CSS_SELECTOR, "a[role='tab'][href*='review'], a[aria-controls*='review']")
#                 )
#             )
#         except TimeoutException:
#             reviewTab = wait.until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., '후기')]")))
#         driver.execute_script("arguments[0].click();", reviewTab)

#         # 리뷰 컨테이너 대기
#         wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.list_review")))

#         # 로딩 루프
#         loadedCount = 0
#         sameCountHit = 0
#         scrollTry = 0

#         while True:
#             # 시간/개수/시도 상한 체크
#             if time.monotonic() - startAt > timeBudget:
#                 break
#             if loadedCount >= maxCount:
#                 break
#             if scrollTry >= scrollLimit:
#                 break

#             soup = BeautifulSoup(driver.page_source, "html.parser")
#             items = soup.select("ul.list_review > li")

#             if len(items) > loadedCount:
#                 loadedCount = len(items)
#                 sameCountHit = 0
#             else:
#                 sameCountHit += 1

#             # 스크롤
#             driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
#             scrollTry += 1
#             time.sleep(0.8)

#             # 더보기 버튼 폴백
#             if sameCountHit >= 2:
#                 try:
#                     moreBtn = driver.find_element(By.CSS_SELECTOR, "a.link_more, button.link_more")
#                     driver.execute_script("arguments[0].click();", moreBtn)
#                     time.sleep(0.8)
#                     sameCountHit = 0
#                 except NoSuchElementException:
#                     break

#         # 최종 파싱
#         soup = BeautifulSoup(driver.page_source, "html.parser")
#         reviewList = soup.select("ul.list_review > li")

#         for li in reviewList[:maxCount]:
#             reviewerName = li.select_one("span.name_user").get_text(strip=True) if li.select_one("span.name_user") else "익명"
#             content = li.select_one("p.desc_review").get_text(strip=True) if li.select_one("p.desc_review") else ""
#             rate = len(li.select(".ico_star.on")) if li.select(".ico_star.on") else 0
#             dateStr = li.select_one(".txt_date").get_text(strip=True) if li.select_one(".txt_date") else None
#             reviewDate = _parseKakaoDate(dateStr)

#             scrapedReviews.append({
#                 "reviewerName": reviewerName,
#                 "content": content,
#                 "rate": rate,
#                 "date": reviewDate,
#             })

#         return scrapedReviews

#     finally:
#         driver.quit()
#         shutil.rmtree(tmpDir, ignore_errors=True)




import time
from datetime import datetime
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

def getKakaoReview(kakaoPlaceId: str) -> list:
    """
    주어진 카카오맵 ID의 리뷰를 스크래핑하여 딕셔너리 리스트로 반환합니다.
    [{"reviewer_name": "...", "content": "...", "rate": 5, "date": "2025.08.20."}, ...]
    """
    url = f"https://place.map.kakao.com/{kakaoPlaceId}"
    
    options = webdriver.ChromeOptions()
    options.add_argument("headless")
    options.add_argument("window-size=1920x1080")
    options.add_argument("user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    scraped_reviews = []

    try:
        print(f"  [Scraper] 페이지 접속: {url}")
        driver.get(url)

        review_tab = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.XPATH, "//a[contains(., '후기')]")))
        driver.execute_script("arguments[0].click();", review_tab)
        
        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, "ul.list_review")))

        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(1.5)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                try:
                    more_button = driver.find_element(By.CSS_SELECTOR, "a.link_more")
                    driver.execute_script("arguments[0].click();", more_button)
                    time.sleep(1.5)
                except:
                    break
            last_height = new_height
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        review_list = soup.select('ul.list_review > li')

        print(f"  [Scraper] {len(review_list)}개의 리뷰 아이템 발견.")
        for item in review_list:
            reviewerName = item.select_one('span.name_user').get_text(strip=True) if item.select_one('span.name_user') else "익명"
            content = item.select_one('p.desc_review').get_text(strip=True) if item.select_one('p.desc_review') else ""
            
            # 별점 추출 (별의 개수로 계산)
            rate = len(item.select('.ico_star.on')) if item.select('.ico_star.on') else 0
            
            # 날짜 추출 및 변환
            date_str = item.select_one('.txt_date').get_text(strip=True) if item.select_one('.txt_date') else None
            review_date = datetime.strptime(date_str, '%Y.%m.%d.') if date_str else datetime.now()

            scraped_reviews.append({
                'reviewerName': reviewerName,
                'content': content,
                'rate': rate,
                'date': review_date,
            })
            
    except Exception as e:
        print(f"  [Scraper] 크롤링 중 에러 발생: {e}")
    finally:
        driver.quit()
        
    return scraped_reviews