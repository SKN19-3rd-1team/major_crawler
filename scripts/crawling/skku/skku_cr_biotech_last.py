from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json


# ============================================
# 1. 학과 정보
# ============================================

# 생명공학대학 (biotech)
BIOTECH_DEPARTMENTS = {
    "식품생명공학과": "food",
    "바이오메카트로닉스학과": "bio"
}

BIOTECH_CURRICULUM_URL = "https://biotech.skku.edu/biotech/course/{}_curriculum.do"

# 융합생명공학과 (skb)
SKB_CURRICULUM_URL = "https://skb.skku.edu/gene/under/under_curriculum.do"

# ============================================
# 2. Selenium 설정
# ============================================

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()


# ============================================
# 3. offset 기반 공통 크롤러 (SW/ICE 방식 그대로)
# ============================================

from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

def crawl_offset_curriculum(url):
    all_subjects = []
    offset = 0
    previous_titles = []

    wait = WebDriverWait(driver, 10)

    while True:
        page_url = f"{url}?pager.offset={offset}&lang=All"
        print(f"\n[페이지 이동] {page_url}")

        driver.get(page_url)

        # 테이블이 로딩될 때까지 대기
        try:
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
        except:
            print("→ 테이블 없음: 종료")
            break

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")
        if len(rows) == 0:
            print("→ 테이블 없음: 종료")
            break

        # 이번 페이지의 제목 리스트
        current_titles = []
        for i in range(0, len(rows), 2):
            try:
                title = rows[i].find_element(By.CSS_SELECTOR, "td:nth-child(2) a").text.strip()
                current_titles.append(title)
            except:
                pass

        # 이전 페이지와 같으면 마지막 페이지로 판단
        if current_titles == previous_titles:
            print("→ 마지막 페이지 도달: 종료")
            break

        previous_titles = current_titles

        # ===== 상세 크롤링 =====
        # ⚠ rows가 클릭 후에 깨질 수 있으니, 매 loop마다 다시 가져오도록 설계
        main_indices = list(range(0, len(rows), 2))

        for main_idx in main_indices:
            try:
                # 매번 새로 rows를 받아서 stale element 방지
                rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

                main_row = rows[main_idx]

                title_elem = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(2) a")
                name = title_elem.text.strip()

                # ⭐ 이수학년: 7번째 컬럼
                try:
                    grade_year = main_row.find_element(By.CSS_SELECTOR, "td:nth-child(7)").text.strip()
                except:
                    grade_year = ""   # 공백이면 그대로 두기

                # 과목명 클릭 (JS 사용으로 가려진 엘리먼트 문제 방지)
                driver.execute_script("arguments[0].click();", title_elem)

                # 클릭 후, 바로 아래 tr(상세설명 row)이 열릴 때까지 대기
                def detail_row_loaded(drv):
                    new_rows = drv.find_elements(By.CSS_SELECTOR, "table tbody tr")
                    if len(new_rows) <= main_idx + 1:
                        return False
                    detail_tr = new_rows[main_idx + 1]
                    td = detail_tr.find_element(By.CSS_SELECTOR, "td")
                    text = td.get_attribute("innerText").strip()
                    # 텍스트 유무와 상관없이 tr이 준비되면 True 리턴
                    return detail_tr

                detail_row = wait.until(detail_row_loaded)

                # 상세설명 추출 (innerText 사용)
                desc_td = detail_row.find_element(By.CSS_SELECTOR, "td")
                desc = desc_td.get_attribute("innerText").strip()

                # 그래도 빈 문자열이면 한번 더 재시도 (약간의 딜레이 후)
                if desc == "":
                    time.sleep(0.3)
                    desc_td = detail_row.find_element(By.CSS_SELECTOR, "td")
                    desc = desc_td.get_attribute("innerText").strip()

                # 여전히 빈값이면 경고 출력 (실제 설명이 없을 가능성)
                if desc == "":
                    print(f"⚠ 설명 없음(빈 문자열): {name}")

                all_subjects.append({
                    "grade_year": grade_year,
                    "name": name,
                    "description": desc
                })

                print(f"[✓] {name} / {grade_year} / desc_len={len(desc)}")

            except Exception as e:
                print(f"❌ 에러 발생 (index={main_idx}): {e}")
                continue

        offset += 30
        if offset > 10000:
            print("→ offset 비정상 증가: 강제 종료")
            break

    return all_subjects




# ============================================
# 4. 전체 실행 (Biotech + SKB)
# ============================================

result = {
    "성균관대학교": {
        "생명공학대학": {},
        "융합생명공학과": []
    }
}

# 생명공학대학 2개 학과
for dept_name, code in BIOTECH_DEPARTMENTS.items():
    print(f"\n========== 생명공학대학 {dept_name} ==========")
    curriculum_url = BIOTECH_CURRICULUM_URL.format(code)
    subjects = crawl_offset_curriculum(curriculum_url)
    result["성균관대학교"]["생명공학대학"][dept_name] = subjects

# 융합생명공학과
print("\n========== 융합생명공학과 ==========")
skb_subjects = crawl_offset_curriculum(SKB_CURRICULUM_URL)
result["성균관대학교"]["융합생명공학과"] = skb_subjects


# JSON 저장
with open("skku_biotech_skb_courses_last.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print("\n🎉 생명공학대학 + 융합생명공학과 전체 크롤링 완료!")
driver.quit()
