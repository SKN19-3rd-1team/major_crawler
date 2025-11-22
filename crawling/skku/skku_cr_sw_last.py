from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

departments = {
    "소프트웨어학과": "sw",
    "컴퓨터공학과": "computer",
    "글로벌융합학부": "global",
    "지능형소프트웨어학과": "intelli"
}

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()

base_curriculum_url = "https://sw.skku.edu/sw/under_{}_curriculum.do"

result_json = {
    "성균관대학교": {
        "소프트웨어융합대학": {}
    }
}

# ----------------------------------------------------------
#  1) SW대학 페이지의 상세스펙: 과목행 + 설명행(2줄 구조)
#     이수학년은 td:nth-child(7)
# ----------------------------------------------------------

def crawl_curriculum_page():

    subjects = []
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    i = 0
    while i < len(rows):

        try:
            main_row = rows[i]
            title_elem = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(2) a")
            name = title_elem.text.strip()

            # ⭐ 이수학년 (컬럼 7)
            grade_year = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text.strip()

            # 상세 내용 펼치기
            driver.execute_script("arguments[0].click();", title_elem)
            time.sleep(0.2)

            # 다음 행이 설명행
            detail_row = rows[i + 1]
            desc = detail_row.find_element(By.CSS_SELECTOR, "td").text.strip()

            subjects.append({
                "grade_year": grade_year,
                "name": name,
                "description": desc
            })

            i += 2

        except:
            i += 1

    return subjects


# ----------------------------------------------------------
#  2) offset 방식 페이지 전체 크롤링
# ----------------------------------------------------------

def crawl_department(dept_name, dept_code):

    print(f"\n===== 학과 크롤링 시작: {dept_name} =====")

    curriculum_url = base_curriculum_url.format(dept_code)
    offset = 0

    previous_titles = []
    all_subjects = []

    while True:
        url = f"{curriculum_url}?pager.offset={offset}&lang=All"
        print(f"[페이지 이동] offset={offset}")

        driver.get(url)
        time.sleep(1.5)

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        if len(rows) == 0:
            print("→ 과목 없음: 종료")
            break

        current_titles = []
        for i in range(0, len(rows), 2):
            try:
                title_elem = rows[i].find_element(By.CSS_SELECTOR, "td:nth-child(2) a")
                current_titles.append(title_elem.text.strip())
            except:
                pass

        if current_titles == previous_titles:
            print("→ 이전 페이지와 동일함: 종료")
            break

        previous_titles = current_titles

        page_subjects = crawl_curriculum_page()
        all_subjects.extend(page_subjects)

        offset += 30
        if offset > 10000:
            print("→ offset 비정상: 종료")
            break

    print(f"총 과목 수집: {len(all_subjects)}개")
    return all_subjects


# ----------------------------------------------------------
#  3) 전체 실행
# ----------------------------------------------------------

college = result_json["성균관대학교"]["소프트웨어융합대학"]

for dept_name, dept_code in departments.items():
    subjects = crawl_department(dept_name, dept_code)
    college[dept_name] = subjects

with open("skku_sw_courses_last.json", "w", encoding="utf-8") as f:
    json.dump(result_json, f, ensure_ascii=False, indent=4)

print("\n🎉 전체 학과 크롤링 완료!")
driver.quit()
