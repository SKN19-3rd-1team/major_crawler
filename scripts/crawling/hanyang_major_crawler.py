from selenium import webdriver
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
        JSON_FILE = f"data/raw/hanyang_syllabus_{semester}.json"

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

                # 조회 버튼 클릭
                btn_find = driver.find_element(By.ID, "btn_Find")
                btn_find.click()

                # 4. 과목명 및 과목 설명 크롤링
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                for row in rows:
                    try:
                        # 학수 번호 클릭 팝업 띄움
                        subject_num = row.find_element(By.ID, "haksuNo")
                        subject_num.click()
                        time.sleep(1)

                        # 팝업 내부 과목명 및 국문개요 크롤링
                        wait.until(EC.visibility_of_element_located((By.ID, "gwamokNm")))

                        subject_name = driver.find_element(By.ID, "gwamokNm").text.strip()
                        description = driver.find_element(By.ID, "gwamokGaeyo").text.strip()
                        print(description)                  
                        
                        # 팝업 닫기
                        close_btn = driver.find_element(By.ID, "btn_Close")
                        close_btn.click()
                        time.sleep(1)
                    except:
                        subject_name = ""
                        description = ""

                    # JSON 구조
                    if college not in data[university_name]:
                        data[university_name][college] = {}
                    if hakgwa_name not in data[university_name][college]:
                        data[university_name][college][hakgwa_name] = []
                    data[university_name][college][hakgwa_name].append({
                        "name": subject_name,
                        "description": description
                    })


        # 5. JSON 저장
        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"JSON 저장 완료: {JSON_FILE}")
    
    driver.quit()

if __name__ == "__main__":
    run()
