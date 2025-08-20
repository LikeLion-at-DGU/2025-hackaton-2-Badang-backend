import time
from django.core.management.base import BaseCommand
from selenium import webdriver
from selenium.common.exceptions import TimeoutException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup

class Command(BaseCommand):
    help = '카카오맵의 리뷰 정보를 크롤링합니다.'

    def handle(self, *args, **options):
        place_id = "13057646" 
        
        # ✅ URL에서 #review 제거
        url = f"https://place.map.kakao.com/{place_id}"

        options = webdriver.ChromeOptions()
        # options.add_argument("headless") 
        options.add_argument("window-size=1920x1080")
        options.add_argument("user-agent=Mozilla/5.0 (Windows NT 1.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36")
        
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        self.stdout.write(self.style.SUCCESS(f"페이지 접속 시도: {url}"))
        driver.get(url)

        # ✅ '후기' 탭 클릭 코드 다시 활성화
        try:
            review_tab = WebDriverWait(driver, 10).until(
                EC.element_to_be_clickable((By.XPATH, "//a[contains(., '후기')]"))
            )
            driver.execute_script("arguments[0].click();", review_tab)
            self.stdout.write(self.style.SUCCESS("'후기' 탭을 클릭했습니다."))
        except TimeoutException:
            self.stderr.write(self.style.ERROR("'후기' 탭을 찾거나 클릭하는 데 실패했습니다."))
            driver.quit()
            return

        try:
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CSS_SELECTOR, "ul.list_review"))
            )
            self.stdout.write(self.style.SUCCESS("리뷰 목록 로딩을 확인했습니다."))
        except TimeoutException:
            self.stderr.write(self.style.ERROR("리뷰 목록을 시간 내에 찾지 못했습니다."))
            with open("debug_page_after_click.html", "w", encoding="utf-8") as f:
                f.write(driver.page_source)
            self.stdout.write(self.style.SUCCESS("클릭 이후의 상황을 'debug_page_after_click.html'에 저장했습니다."))
            driver.quit()
            return
        
        # (이하 스크롤 및 파싱 코드는 동일)
        last_height = driver.execute_script("return document.body.scrollHeight")
        self.stdout.write(self.style.SUCCESS("전체 리뷰 로드를 위해 스크롤 시작..."))
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
                    self.stdout.write(self.style.SUCCESS("모든 리뷰 로드 완료."))
                    break
            last_height = new_height
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')

        review_list = soup.select('ul.list_review > li')

        if not review_list:
            self.stderr.write(self.style.ERROR("리뷰를 찾을 수 없습니다."))
        else:
            self.stdout.write(self.style.SUCCESS(f"\n총 {len(review_list)}개의 리뷰를 수집했습니다."))
            self.stdout.write("-" * 50)
            for i, review in enumerate(review_list):
                reviewer_name_tag = review.select_one('span.name_user')
                reviewer_name = reviewer_name_tag.get_text(strip=True) if reviewer_name_tag else "이름 없음"
                
                review_content_tag = review.select_one('p.desc_review')
                review_content = review_content_tag.get_text(strip=True) if review_content_tag else "내용 없음"
                
                self.stdout.write(f"[{i+1:03d}] 👤 이름: {reviewer_name}")
                self.stdout.write(f"💬 내용: {review_content}")
                self.stdout.write("-" * 50)

        driver.quit()