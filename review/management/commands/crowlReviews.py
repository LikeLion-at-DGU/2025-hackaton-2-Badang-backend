import time
import warnings
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

from django.core.management.base import BaseCommand
from review.models import Review, Reviewer
from main.models import Store

warnings.filterwarnings("ignore")

class Command(BaseCommand):
    place_id = 20172343

    url = f"https://map.kakao.com/{place_id}/#reviews"
    driver = webdriver.Chrome(ChromeDriverManager().install())
    driver.get(url)

    time.sleep(5)

    driver.find_element(By.XPATH, '//*[@id="info.search.place.list"]/li[2]/a').send_keys(Keys.ENTER)

    reviewList = []

    def extract_review():
        html = Command.driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        review_lists = soup.select('.list_evaluation > li')
        
        count = 0
        reviews = []

        if len(review_lists) != 0:
            for review in review_lists:
                comment = review.select('.txt_comment > span')[0].text
                if len(comment) > 0:
                    reviews.append(comment)
        else:
            reviews.append(' ')
            
        driver.close()
        driver.switch_to.window(driver.window_handles[0])
        time.sleep(2)
        
        return reviews

    def reviewNamePrint():
        time.sleep(0.2)
        
        html = driver.page_source
        soup = BeautifulSoup(html, 'html.parser')
        
        place_lists = soup.select('.placeList > .placeItem')

        for i, place in enumerate(place_lists):
            temp = []
            
            name = place.select('head_item > .tit_name > .link_name')[0].text
            score = place.select('.rating > .score > em')[0].text
            addr = place.select('.addr > p')[0].text
            
            # 상세정보 탭으로 이동
            driver.find_element(By.XPATH, r'//*[@id="info.search.place.list"]/li['+str(i+1)+']/div[5]/div[4]/a[1]').send_keys(Keys.ENTER)
            driver.switch_to.window(driver.window_handles[-1])
            time.sleep(2)
            rev = extract_review()  # 리뷰 추출 함수 실행
            
            
            # 하나의 리스트로 만들어 room_list에 추가
            temp.append(name)
            temp.append(score)
            temp.append(addr[3:])
            temp.append(rev)
            
            room_list.append(temp)

    def getReviewList():
        global reviewList
        review_elements = driver.find_elements(By.CLASS_NAME, "review")
        for review in review_elements:
            reviewer_name = review.find_element(By.CLASS_NAME, "reviewer-name").text
            review_text = review.find_element(By.CLASS_NAME, "review-text").text
            reviewList.append(Review(reviewer=Reviewer(name=reviewer_name), text=review_text))
        return reviewList

    for i in range(1, 9):
        try:
            page2 += 1
            print(page, 'page')
            
            # 페이지 버튼 번호(1에서 5 사이 값)
            if i > 5:
                xpath = '/html/body/div[5]/div[2]/div[1]/div[7]/div[6]/div/a['+str(i-5)+']'
            else:
                xpath = '/html/body/div[5]/div[2]/div[1]/div[7]/div[6]/div/a['+str(i)+']'
            
            driver.find_element(By.XPATH, xpath).send_keys(Keys.ENTER)  # 페이지 선택
            reviewNamePrint()  # 리뷰 정보 크롤링


            # page2가 5를 넘어가면 다시 1로 바꿔주고 다음 버튼 클릭
            if page2 > 5:
                page2 = 1
                driver.find_element(By.XPATH, r'//* [@id="info.search.page.next"]').send_keys(Keys.ENTER)
            
            page += 1
        
        except:
            break
            
    print('크롤링 완료')