from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
import json

# ============================================
# 1. 자연과학대학 학과 정보
# ============================================

NATSCI_DEPARTMENTS = {
    "생명과학과": "bio",
    "수학과": "math",
    "물리학과": "physics",
    "화학과": "chem"
}

NATSCI_CURRICULUM_URL = "https://cscience.skku.edu/cscience/undergraduate/{}_curiculum.do"


# ============================================
# 2. selenium 기본 설정
# ============================================

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()

wait = WebDriverWait(driver, 10)

# ============================================
# 3. 안정형 Offset 크롤러 (이수학년 포함)
# ============================================

def crawl_offset_curriculum(url):
    all_subjects = []
    offset = 0
    previous_titles = []

    while True:
        page_url = f"{url}?pager.offset={offset}&lang=All"
        print(f"\n=== 페이지 이동 offset={offset} ===")
        driver.get(page_url)

        # 테이블 로딩 대기
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        except:
            print("→ 테이블 없음: 종료")
            break

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        if len(rows) == 0:
            print("→ 테이블 없음: 종료")
            break

        # 페이지 제목 리스트 추출
        current_titles = []
        for i in range(0, len(rows), 2):
            try:
                title = rows[i].find_element(By.CSS_SELECTOR, "td:nth-child(2) a").text.strip()
                current_titles.append(title)
            except:
                pass

        # 반복 감지 → 종료
        if current_titles == previous_titles:
            print("→ 마지막 페이지 도달: 종료")
            break

        previous_titles = current_titles

        # 상세 크롤링
        main_indices = list(range(0, len(rows), 2))

        for main_idx in main_indices:
            try:
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
                main_row = rows[main_idx]

                title_elem = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(2) a")
                name = title_elem.text.strip()

                # ⭐ 이수학년 (7번째 컬럼)
                try:
                    grade_year = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text.strip()
                except:
                    grade_year = ""

                # 상세보기 클릭
                driver.execute_script("arguments[0].click();", title_elem)

                # 상세 row 로딩 대기
                def detail_loaded(drv):
                    new_rows = drv.find_elements(By.CSS_SELECTOR, "table tbody tr")
                    if len(new_rows) <= main_idx + 1:
                        return False
                    detail_tr = new_rows[main_idx + 1]
                    return detail_tr

                detail_row = wait.until(detail_loaded)
                desc_td = detail_row.find_element(By.CSS_SELECTOR, "td")

                # ⭐ description 안정적으로 수집
                desc = desc_td.get_attribute("innerText").strip()

                if desc == "":
                    time.sleep(0.2)
                    desc = desc_td.get_attribute("innerText").strip()

                if desc == "":
                    print(f"⚠ 설명 없음: {name}")

                print(f"[✓] {name} / {grade_year} / desc_len={len(desc)}")

                all_subjects.append({
                    "grade_year": grade_year,
                    "name": name,
                    "description": desc
                })

            except Exception as e:
                print(f"❌ 에러 발생: {e}")
                continue

        offset += 30
        if offset > 10000:
            print("→ offset 비정상 증가: 강제 종료")
            break

    return all_subjects


# ============================================
# 4. 전체 자연과학대학 크롤링 실행
# ============================================

result = {
    "성균관대학교": {
        "자연과학대학": {}
    }
}

print("\n================ 자연과학대학 크롤링 시작 ================\n")

for dept_name, code in NATSCI_DEPARTMENTS.items():

    print(f"\n========== {dept_name} ==========")
    curriculum_url = NATSCI_CURRICULUM_URL.format(code)

    subjects = crawl_offset_curriculum(curriculum_url)
    result["성균관대학교"]["자연과학대학"][dept_name] = subjects


# JSON 저장
with open("skku_natural_science_courses_last.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print("\n🎉 자연과학대학 전체 크롤링 완료!")
driver.quit()
