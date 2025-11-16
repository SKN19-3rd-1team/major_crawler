from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

url = "https://portal.hanyang.ac.kr/sugang/sulg.do"
university_name = "한양대학교"
semesters = [1, 2]
colleges = ["공과대학", "자연과학대학"]


def get_popup_text(driver, suup_no):
    """과목코드(suupNo2)로 팝업 URL 열고 텍스트 추출"""
    popup_url = (
        "https://portal.hanyang.ac.kr/openPop.do?header=hidden"
        f"&url=/haksa/SughAct/findSuupPlanDocHyIn.do&flag=DN&year=2025&term=10"
        f"&suup={suup_no}&language=ko"
    )

    driver.execute_script(f"window.open('{popup_url}', '_blank');")
    driver.switch_to.window(driver.window_handles[-1])
    time.sleep(1)

    text = ""
    try:
        body = driver.find_element(By.TAG_NAME, "body")
        text = body.text.strip()
    except:
        text = ""

    driver.close()
    driver.switch_to.window(driver.window_handles[0])
    return text


def run():
    # 1. Chrome 실행
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service)

    driver.get(url)
    wait = WebDriverWait(driver, 10)

    # 2. Syllabus 페이지 접속
    syllabus_link = WebDriverWait(driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//a[@title="수강편람"]')))
    driver.execute_script("arguments[0].click();", syllabus_link)
    time.sleep(1)

    # 3. 검색 조건 설정
    for semester in semesters:
        data = {university_name: {}}
        JSON_FILE = f"data/raw/hanyang_syllabus_{semester}.json"

        for college in colleges:
            # 학기 선택
            term_select_element = wait.until(EC.visibility_of_element_located((By.ID, "cbHakgi")))
            term_select = Select(term_select_element)
            term_select.select_by_visible_text(f"{semester}학기")
            time.sleep(1)

            # 학과과목(전공) 오디오버튼 선택
            major_radio = WebDriverWait(driver, 10).until(EC.element_to_be_clickable((By.ID, "rdoJongmok2")))
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
                hakgwa_value = hakgwa_option.get_attribute("value")

                data[university_name][college].setdefault(hakgwa_name, [])

                hakgwa_select.select_by_value(hakgwa_value)

                # 조회 버튼 클릭
                btn_find = driver.find_element(By.ID, "btn_Find")
                btn_find.click()

                WebDriverWait(driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "table tbody tr")))

                # 4. 과목명 및 과목 설명 크롤링
                # 학수 번호 클릭
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

                for row in rows:
                    try:
                        suup_no = row.find_element(By.ID, "suupNo2").text.strip()
                        subject_name = row.find_element(By.ID, "gwamokNm").text.strip() # 과목명
                    except:
                        continue

                    # 과목 국문개요 
                    description = get_popup_text(driver, suup_no)

                    # JSON 구조에 맞게 저장
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
