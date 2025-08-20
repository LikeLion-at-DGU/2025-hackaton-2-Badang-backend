# review/getReview.py

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

def getKakaoReview(kakao_place_id: str) -> list:
    """
    주어진 카카오맵 ID의 리뷰를 스크래핑하여 딕셔너리 리스트로 반환합니다.
    [{"reviewer_name": "...", "content": "...", "rate": 5, "date": "2025.08.20."}, ...]
    """
    url = f"https://place.map.kakao.com/{kakao_place_id}"
    
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