import time
import warnings
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from django.core.management.base import BaseCommand
from review.models import Review, Reviewer
from main.models import Store

warnings.filterwarnings("ignore")

class Command(BaseCommand):
    help = "카카오맵 리뷰 크롤러"

    def add_arguments(self, parser):
        parser.add_argument("--store_id", type=str, help="카카오맵 storeId")

    def handle(self, *args, **options):
        store_id = options['store_id']
        if not store_id:
            self.stdout.write(self.style.ERROR("store_id가 필요합니다."))
            return

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
        url = f"https://place.map.kakao.com/{store_id}#review"
        driver.get(url)
        
        self.stdout.write(self.style.SUCCESS("페이지 로드 후 스크롤을 시작합니다."))
        time.sleep(5)  # 페이지 로딩 대기

        # 스크롤 내리면서 리뷰 로딩
        last_height = driver.execute_script("return document.body.scrollHeight")
        while True:
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            new_height = driver.execute_script("return document.body.scrollHeight")
            if new_height == last_height:
                break
            last_height = new_height
            
        # Selenium을 사용하여 리뷰 elements 찾기
        try:
            # 리뷰 목록이 로드될 때까지 최대 10초 대기
            WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, ".list_review > li"))
            )
            review_items = driver.find_elements(By.CSS_SELECTOR, ".list_review > li")
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"리뷰 elements를 찾을 수 없습니다: {e}"))
            review_items = []
        
        if not review_items:
            self.stdout.write(self.style.WARNING("리뷰가 없습니다."))
            driver.quit()
            return

        store = Store.objects.filter(kakao_place_id=store_id).first()
        if not store:
            self.stdout.write(self.style.WARNING(f"스토어 ID {store_id}를 찾을 수 없습니다."))
            driver.quit()
            return
            
        for item in review_items:
            # 리뷰어 이름: .txt_username (스크린샷 기반)
            try:
                reviewer_name = item.find_element(By.CSS_SELECTOR, ".txt_username").text.strip()
            except:
                reviewer_name = "익명"

            # 리뷰 내용: .txt_comment (스크린샷 기반)
            try:
                comment = item.find_element(By.CSS_SELECTOR, ".txt_comment").text.strip()
            except:
                comment = None

            # 리뷰 점수: .num_rate (스크린샷 기반)
            try:
                score = item.find_element(By.CSS_SELECTOR, ".num_rate").text.strip()
            except:
                score = None

            reviewer, _ = Reviewer.objects.get_or_create(name=reviewer_name)

            Review.objects.create(
                reviewer=reviewer,
                text=comment,
                score=score,
                store=store
            )

        self.stdout.write(self.style.SUCCESS(f"{len(review_items)}개의 리뷰를 성공적으로 크롤링했습니다."))
        driver.quit()