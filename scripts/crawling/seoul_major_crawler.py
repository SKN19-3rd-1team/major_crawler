from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

url = "https://sugang.snu.ac.kr/sugang/co/co010.action"
university_name = "서울대학교"
semesters = [1, 2]
colleges = ["공과대학", "자연과학대학"]

def run():
    # 1. Chrome 실행
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    driver.get(url)
    wait = WebDriverWait(driver, 10)

    # 2. 검색 조건 설정
    for semester in semesters:
        data = {university_name: {}}
        JSON_FILE = f"data/raw/seoul_syllabus_{semester}.json"

        for college in colleges:
            # 검색 조건 설정 버튼 클릭
            btn_detail = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.total-filter-btn")))
            driver.execute_script("arguments[0].click();", btn_detail)
            time.sleep(1)

            # 이전학기 검색조건 버튼 클릭
            if semester == semesters[0] and college == colleges[0]:
                btn_prev = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "button.view-last-semester-btn")))
                driver.execute_script("arguments[0].click();", btn_prev)
                time.sleep(1)

                # 학사 선택
                degree_select = Select(driver.find_element(By.ID, "hSrchCptnCorsFg"))
                degree_select.select_by_visible_text("학사")
                time.sleep(1)

                # 교과 선택
                driver.find_element(By.CSS_SELECTOR, "input[value='B']").click()  # 전필
                driver.find_element(By.CSS_SELECTOR, "input[value='C']").click()  # 전선
                time.sleep(1)

            # 학기 선택
            semester_select = Select(driver.find_element(By.ID, "hSrchOpenShtm"))
            semester_select.select_by_visible_text(f"{semester}학기")
            time.sleep(1)

            # 단과대학 선택
            college_select = Select(driver.find_element(By.ID, "hSrchOpenUpDeptCd"))
            college_select.select_by_visible_text(college)
            time.sleep(1)

            # 검색 버튼 클릭
            search_btn = driver.find_element(By.CSS_SELECTOR, ".filter-submit-btn")
            driver.execute_script("arguments[0].click();", search_btn)
            time.sleep(1)

            previous_page = None

            # 3. 과목명 및 과목 설명 크롤링
            while True:
                current_page = int(driver.find_element(By.CSS_SELECTOR, ".cc-paging a.num.on").text)
                print("현재 페이지:", current_page)

                if previous_page == current_page:
                    break

                # 현재 페이지 과목 목록
                courses = driver.find_elements(By.CSS_SELECTOR, ".course-info-item")
                
                for course in courses:
                    # 과목명
                    course_name = course.find_element(By.CSS_SELECTOR, ".course-name strong").text.strip()

                    # 과목 리스트 클릭
                    detail_btn = course.find_element(By.CSS_SELECTOR, "a.course-info-detail")
                    driver.execute_script("arguments[0].click();", detail_btn)
                    time.sleep(1)

                    # 학과명
                    dept_name = driver.find_element(By.ID, "deptKorNm").text.strip()

                    try:
                        # 강의계획서 버튼 클릭 -> 수업 목표
                        # tab_lecture_plan = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#tab3 button")))
                        # driver.execute_script("arguments[0].click();", tab_lecture_plan)
                        # description = wait.until(EC.presence_of_element_located((By.ID, "ltPurp"))).text.strip()
                        
                        # 교과목개요 버튼 클릭 -> 교과목개요(국문)
                        tab_outline = wait.until(EC.element_to_be_clickable((By.CSS_SELECTOR, "#tab2 button")))
                        driver.execute_script("arguments[0].click();", tab_outline)
                        description = wait.until(EC.presence_of_element_located((By.ID, "sbjtSmryCtnt"))).text.strip()
                    except:
                        description = ""

                    # JSON 구조에 맞게 저장
                    if college not in data[university_name]:
                        data[university_name][college] = {}
                    if dept_name not in data[university_name][college]:
                        data[university_name][college][dept_name] = []

                    data[university_name][college][dept_name].append({
                        "name": course_name,
                        "description": description
                    })

                # 다음 페이지 클릭
                next_page = driver.find_elements(By.CSS_SELECTOR, f'.cc-paging a.num[href*="fnGotoPage({current_page + 1})"]')
                if next_page:
                    driver.execute_script("arguments[0].click();", next_page[0])
                else:
                    next_arrow = driver.find_element(By.CSS_SELECTOR, ".cc-paging a.arrow.next")
                    if "disabled" in next_arrow.get_attribute("class"):
                        previous_page = current_page
                        continue 
                    else:
                        driver.execute_script("arguments[0].click();", next_arrow)
                
                time.sleep(1)
                previous_page = current_page
                    
        # 4. 학기별 JSON 저장
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            print('저장: ', JSON_FILE)

    driver.quit()

if __name__ == "__main__":
    run()