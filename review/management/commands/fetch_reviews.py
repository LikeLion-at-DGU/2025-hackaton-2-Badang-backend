# review/management/commands/fetch_reviews.py
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
    help = "Fetch reviews from Kakao Map and save to DB"

    def handle(self, *args, **kwargs):
        url = "https://map.kakao.com/"
        chrome_service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=chrome_service)
        driver.get(url)

        wait = WebDriverWait(driver, 15)

        # helper functions
        def dump_page(filename='tmp_place_page.html'):
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(driver.page_source)
                print(f"페이지 소스 저장: {filename}")
            except Exception as e:
                print("페이지 저장 실패:", e)

        def parse_review_block(item):
            # item: bs4.element.Tag representing one review block
            # try several selectors for author
            author_selectors = [
                'a.link_profile',
                'a.link_name',
                '.info_review a',
                '.info_user a',
                '.nick',
                '.name',
                'strong',
            ]
            author = ''
            for sel in author_selectors:
                tag = item.select_one(sel)
                if tag and tag.get_text(strip=True):
                    author = tag.get_text(strip=True)
                    break

            # try several selectors for review text
            text_selectors = [
                '.txt_comment > span',
                '.txt_comment',
                '.comment',
                '.review_txt',
                '.section_review .inner_review',
            ]
            text = ''
            for sel in text_selectors:
                ttag = item.select_one(sel)
                if ttag:
                    t = ttag.get_text(separator=' ', strip=True)
                    if t and len(t) > 0:
                        text = t
                        break

            # fallback: use all text inside the review item but strip common noise
            if not text:
                t = item.get_text(separator=' ', strip=True)
                # remove author text if present
                if author and t.startswith(author):
                    t = t[len(author):].strip()
                text = t

            return {'author': author, 'text': text}


        def extract_reviews():
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            review_items = soup.select('.list_evaluation > li')
            reviews = []
            for item in review_items:
                parsed = parse_review_block(item)
                # skip empty texts
                if parsed['text']:
                    reviews.append(parsed)
            return reviews

        def extract_representative_reviews():
            html = driver.page_source
            soup = BeautifulSoup(html, 'html.parser')
            # try to find representative review blocks using a few container selectors
            candidates = []
            container_selectors = [
                '.group_review .list_review li',
                '.section_review .inner_review',
                '.inner_review',
                '.list_review li',
                '.list_evaluation > li',
            ]
            for sel in container_selectors:
                found = soup.select(sel)
                if found:
                    for f in found:
                        candidates.append(f)
                if candidates:
                    break

            results = []
            for item in candidates:
                parsed = parse_review_block(item)
                if parsed['text'] and len(parsed['text']) > 5:
                    results.append(parsed)

            # deduplicate by text
            seen = set()
            unique = []
            for r in results:
                key = r['text']
                if key not in seen:
                    seen.add(key)
                    unique.append(r)
            return unique

        def load_all_reviews(max_scrolls=30, pause=1.0):
            last_count = 0
            for i in range(max_scrolls):
                items = driver.find_elements(By.CSS_SELECTOR, '.list_evaluation > li')
                count = len(items)
                print(f"스크롤 시도 {i+1}: 리뷰 개수 = {count}")
                if count == last_count and count > 0:
                    break
                last_count = count
                driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')
                time.sleep(pause)

        def expand_all_review_more_buttons():
            try:
                buttons = driver.find_elements(By.XPATH, "//a[contains(normalize-space(.), '더보기') or contains(@class,'link_more')]")
                print(f"확장 가능한 내부 '더보기' 버튼 수: {len(buttons)}")
                for b in buttons:
                    try:
                        driver.execute_script('arguments[0].scrollIntoView(true);', b)
                        driver.execute_script('arguments[0].click();', b)
                        time.sleep(0.2)
                    except Exception:
                        pass
            except Exception as e:
                print('내부 더보기 확장 중 오류:', e)

        try:
            # 검색창 입력
            search_area = wait.until(
                EC.presence_of_element_located((By.XPATH, '//*[@id="search.keyword.query"]'))
            )
            search_area.send_keys("길없음")
            search_area.send_keys(Keys.ENTER)

            # iframe이면 전환
            try:
                iframe = WebDriverWait(driver, 5).until(
                    EC.presence_of_element_located((By.ID, "searchIframe"))
                )
                driver.switch_to.frame(iframe)
            except Exception:
                pass

            # 상세보기 진입
            moreview_links = WebDriverWait(driver, 10).until(
                EC.presence_of_all_elements_located((By.CSS_SELECTOR, "a[data-id='moreview']"))
            )
            if not moreview_links:
                print("상세보기 링크 없음")
                return

            link = moreview_links[0]
            href = link.get_attribute('href')
            driver.execute_script("arguments[0].scrollIntoView(true);", link)
            if href and '/place/' in href:
                try:
                    driver.get(href)
                    print(f"직접 이동: {href}")
                    try:
                        place_id = href.split('/place/')[-1].split('?')[0]
                        print(f"place_id: {place_id}")
                    except Exception:
                        pass
                except Exception as e:
                    print("직접 이동 실패, 클릭 시도:", e)
                    try:
                        driver.execute_script("arguments[0].click();", link)
                    except Exception:
                        pass
            else:
                try:
                    driver.execute_script("arguments[0].click();", link)
                except Exception:
                    driver.execute_script("arguments[0].dispatchEvent(new MouseEvent('click',{bubbles:true}))", link)

            time.sleep(2)
            try:
                driver.switch_to.default_content()
            except Exception:
                pass

            try:
                WebDriverWait(driver, 10).until(EC.url_contains('/place/'))
            except Exception:
                pass

            # 후기 탭 찾기
            found = False
            review_tab_opened = False
            try:
                try:
                    driver.switch_to.default_content()
                except Exception:
                    pass

                tab_groups = driver.find_elements(By.CSS_SELECTOR, "ul.list_tab")
                print(f"DEBUG: ul.list_tab 개수 = {len(tab_groups)}")
                for group_idx, tab_group in enumerate(tab_groups):
                    a_tags = tab_group.find_elements(By.TAG_NAME, "a")
                    for a_idx, a in enumerate(a_tags):
                        try:
                            js_text = driver.execute_script("return arguments[0].textContent", a) or ''
                        except Exception:
                            js_text = ''
                        href = a.get_attribute('href')
                        print(f"ul.list_tab #{group_idx} a[{a_idx}]: text='{a.text.strip()}', js_text='{js_text.strip()}', href='{href}'")
                        try:
                            if href and href.endswith('#review'):
                                driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", a)
                                time.sleep(1)
                                found = True
                                review_tab_opened = True
                                break
                            if js_text and '후기' in js_text:
                                driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", a)
                                time.sleep(1)
                                found = True
                                review_tab_opened = True
                                break
                        except Exception as e:
                            print("탭 클릭 실패(개별):", e)
                    if found:
                        break

                # 폴백: document.querySelector
                if not found:
                    try:
                        el = driver.execute_script("return document.querySelector(\"a[href$='#review'], a[href*='#review']\");")
                        if el:
                            driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", el)
                            print("JS querySelector로 클릭함 (a[href*='#review'])")
                            time.sleep(1)
                            found = True
                            review_tab_opened = True
                    except Exception as e:
                        print("document.querySelector 예외:", e)

                # iframe 내부 탐색
                if not found:
                    iframes = driver.find_elements(By.TAG_NAME, 'iframe')
                    print(f"DEBUG: iframe 개수 = {len(iframes)}")
                    for idx, fr in enumerate(iframes):
                        try:
                            driver.switch_to.frame(fr)
                            elems = driver.find_elements(By.CSS_SELECTOR, "ul.list_tab")
                            for g_idx, g in enumerate(elems):
                                a_tags = g.find_elements(By.TAG_NAME, 'a')
                                for a_idx, a in enumerate(a_tags):
                                    js_text = driver.execute_script("return arguments[0].textContent", a) or ''
                                    href = a.get_attribute('href')
                                    print(f"iframe #{idx} a[{a_idx}]: js_text='{js_text.strip()}', href='{href}'")
                                    try:
                                        if (href and href.endswith('#review')) or ('후기' in js_text):
                                            driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", a)
                                            time.sleep(1)
                                            found = True
                                            review_tab_opened = True
                                            break
                                    except Exception as e:
                                        print(f"iframe 내부 클릭 실패:{e}")
                                if found:
                                    break
                            driver.switch_to.default_content()
                            if found:
                                break
                        except Exception as e:
                            print(f"iframe #{idx} 탐색 실패:", e)
                            try:
                                driver.switch_to.default_content()
                            except Exception:
                                pass
            except Exception as e:
                print("후기 탭 검색 예외:", e)

            # 후기 더보기 버튼 탐색 및 처리
            reviews_texts = []
            try:
                patterns = [
                    "//a[contains(normalize-space(.), '후기 더보기')]|//button[contains(normalize-space(.), '후기 더보기')]",
                    "//a[contains(normalize-space(.), '후기 더보기')]",
                    "//button[contains(normalize-space(.), '후기 더보기')]",
                ]
                more_button = None
                for p in patterns:
                    elems = driver.find_elements(By.XPATH, p)
                    if elems:
                        more_button = elems[0]
                        print(f"후기 더보기 버튼 발견 패턴: {p}")
                        break

                if more_button:
                    try:
                        driver.execute_script("arguments[0].scrollIntoView(true); arguments[0].click();", more_button)
                        time.sleep(1)
                        try:
                            WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.list_evaluation > li')))
                        except Exception:
                            pass
                        load_all_reviews()
                        expand_all_review_more_buttons()
                        reviews_texts = extract_reviews()
                        print("'후기 더보기' 클릭 후 전체 후기 수집 시도")
                    except Exception as e:
                        print("후기 더보기 클릭 실패, 대표 리뷰 시도:", e)
                        reviews_texts = extract_representative_reviews()
                else:
                    if review_tab_opened:
                        try:
                            load_all_reviews()
                            expand_all_review_more_buttons()
                            reviews_texts = extract_reviews()
                            print("후기 탭 열림 감지 — 전체 후기 수집 시도")
                        except Exception as e:
                            print('후기 탭 열림 후 전체 로드 실패:', e)
                            reviews_texts = extract_representative_reviews()
                    else:
                        print("'후기 더보기' 버튼 없음 — 대표 리뷰 추출")
                        reviews_texts = extract_representative_reviews()
            except Exception as e:
                print("후기 더보기 처리 중 예외:", e)
                reviews_texts = extract_representative_reviews()

            # 결과 출력
            print("=== 크롤링된 리뷰 ===")
            for i, r in enumerate(reviews_texts, start=1):
                author = r.get('author','')
                text = r.get('text','')
                if author:
                    print(f"{i}. 작성자: {author}")
                    print(f"   후기: {text}")
                else:
                    print(f"{i}. 후기: {text}")
            print("=====================")

        except Exception as e:
            print("후기 탭 클릭 실패:", e)
            try:
                dump_page('tmp_place_page.html')
                print("모든 탐색 시도 후에도 '후기' 탭을 찾지 못했습니다. 전체 페이지를 tmp_place_page.html로 저장했습니다.")
            except Exception:
                pass
        finally:
            try:
                print("크롤링 종료 — 브라우저 닫는 중...")
                driver.quit()
            except Exception:
                pass
