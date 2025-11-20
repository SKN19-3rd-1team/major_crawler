from selenium import webdriver
from selenium.webdriver import ActionChains
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json
# playwright

url = "https://portal.hanyang.ac.kr/sugang/sulg.do"
university_name = "한양대학교"
semesters = [1, 2]
colleges = ["공과대학", "자연과학대학"]

def run():
    # 1. Chrome 실행
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    driver.get(url)
    wait = WebDriverWait(driver, 10)

    # 2. Syllabus 페이지 접속
    syllabus_link = wait.until(EC.element_to_be_clickable((By.XPATH, '//a[@title="수강편람"]')))
    driver.execute_script("arguments[0].click();", syllabus_link)
    time.sleep(1)

    # 3. 검색 조건 설정
    for semester in semesters:
        data = {university_name: {}}
        JSON_FILE = f"data/raw/hanyang_syllabus_add_{semester}.json"

        for college in colleges:
            # 학기 선택
            term_select_element = wait.until(EC.visibility_of_element_located((By.ID, "cbTerm")))
            term_select = Select(term_select_element)
            term_select.select_by_visible_text(f"{semester}학기")
            time.sleep(1)

            # 학과과목(전공) 오디오버튼 선택
            major_radio = wait.until(EC.element_to_be_clickable((By.ID, "hak")))
            major_radio.click()
            time.sleep(1)

            # 단과대학 선택
            daehak_select = Select(driver.find_element(By.ID, "cbDaehak"))
            daehak_select.select_by_visible_text(college)
            time.sleep(1)
            
            # 학과 선택
            hakgwa_select = Select(driver.find_element(By.ID, "cbHakgwajungong"))

            for hakgwa_option in hakgwa_select.options:
                hakgwa_name = hakgwa_option.text.strip()
                hakgwa_select.select_by_visible_text(hakgwa_name)
                time.sleep(1)

                # 조회 버튼 클릭
                btn_find = driver.find_element(By.ID, "btn_Find")
                btn_find.click()
                time.sleep(1)

                previous_page = None

                while True:
                    # wait.until(lambda driver: driver.find_element(By.CSS_SELECTOR, ".numberLink span.strong").text.strip() != "")
                    paging = driver.find_element(By.CSS_SELECTOR, ".numberLink")
                    current_page = int(paging.find_element(By.CSS_SELECTOR, "span.strong").text.strip())
                    print("현재 페이지: ", current_page)

                    if previous_page == current_page:
                        break

                    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                    for row in rows:
                        grade = ""
                        course_classification = ""
                        subject_name = ""
                        description = ""

                        # 학년
                        try:
                            grade = row.find_elements(By.CSS_SELECTOR, "td#isuGrade")[0].text.strip()
                        except:
                            grade = ""

                        # 과목 분류
                        try:
                            course_classification = row.find_elements(By.CSS_SELECTOR, "td#isuGbNm")[0].text.strip()
                        except:
                            course_classification = ""

                        # 과목명
                        try:
                            subject_name = row.find_elements(By.CSS_SELECTOR, "td#gwamokNm")[0].text.strip()
                        except:
                            subject_name = ""

                        try:
                            # 4. 학수번호 클릭 (팝업 오픈)
                            subject_num = row.find_element(By.ID, "haksuNo")
                            driver.execute_script("arguments[0].click();", subject_num)
                            time.sleep(1)

                            # 과목 설명 크롤링
                            try:
                                description = driver.find_element(By.ID, "gwamokGaeyo").text.strip()
                            except:
                                description = ""                        
                        except Exception as e:
                            print("에러:", e)

                        if subject_name.strip() or description.strip():
                            if college not in data[university_name]:
                                data[university_name][college] = {}
                            if hakgwa_name not in data[university_name][college]:
                                data[university_name][college][hakgwa_name] = []
                            data[university_name][college][hakgwa_name].append({
                                "grade_semester": f'{grade}-{semester}',
                                "course_classification": course_classification,
                                "name": subject_name,
                                "description": description
                            })

                            print(f'{grade}-{semester}')
                            print(f'{course_classification}\n{subject_name}')
                        else:
                            print(f"빈 항목 건너뜀")

                    # 팝업 닫기
                    close_btn = driver.find_element(By.ID, "btn_Close")
                    driver.execute_script("arguments[0].click();", close_btn)
                    time.sleep(1)

                    # 다음 페이지 클릭
                    next_page = driver.find_elements(By.CSS_SELECTOR,f'.cc-paging a[onclick="ServiceController.goPage({current_page + 1})"]')
                    if next_page:
                        driver.execute_script("arguments[0].click();", next_page[0])
                    else:
                        next_arrow = driver.find_element(By.CSS_SELECTOR, '#pagingPanel img[alt="다음"]')
                        driver.execute_script("arguments[0].click();", next_arrow)
                            
                    time.sleep(1)
                    previous_page = current_page

                with open(JSON_FILE, "w", encoding="utf-8") as f:
                    json.dump(data, f, ensure_ascii=False, indent=2)
                    print(f"중간 저장 완료: {JSON_FILE}")

        # 5. JSON 저장
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"JSON 저장 완료: {JSON_FILE}")
    
    driver.quit()

if __name__ == "__main__":
    run()