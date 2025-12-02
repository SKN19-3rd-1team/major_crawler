from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import json

# ============================================
# 1. 학과 정보
# ============================================

ICE_DEPARTMENTS = {
    "전자전기공학부": "eee",
    "반도체시스템공학과": "semi",
    "소재부품융합공학과": "mcce"
}

ICE_CURRICULUM_URL = "https://ice.skku.edu/ice/dept_{}_course.do"
SCE_URL = "https://sce.skku.edu/sce/dept_curriculum.do"

# ============================================
# 2. Selenium 설정
# ============================================

driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()))
driver.maximize_window()

# ============================================
# 3. ICE(정보통신대학) offset 방식 크롤러
#    ⭐ 이수학년 = td[6] = nth-child(7)
# ============================================

def crawl_offset_curriculum(url):
    all_subjects = []
    offset = 0
    previous_titles = []

    while True:
        page_url = f"{url}?pager.offset={offset}&lang=All"
        print(f"\n[페이지 이동] {page_url}")

        driver.get(page_url)
        time.sleep(1.3)

        rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

        if len(rows) == 0:
            print("→ 테이블 없음: 종료")
            break

        # 페이지의 전체 과목명 리스트
        current_titles = []
        for i in range(0, len(rows), 2):
            try:
                title = rows[i].find_element(By.CSS_SELECTOR, "td:nth-child(2) a").text.strip()
                current_titles.append(title)
            except:
                pass

        if current_titles == previous_titles:
            print("→ 마지막 페이지: 종료")
            break

        previous_titles = current_titles

        # 상세 크롤링
        i = 0
        while i < len(rows):
            try:
                title_elem = rows[i].find_element(By.CSS_SELECTOR, "td:nth-child(2) a")
                name = title_elem.text.strip()

                # ⭐ 이수학년 = 7번째 컬럼
                grade_year = rows[i].find_element(By.CSS_SELECTOR, "td:nth-child(7)").text.strip()

                # 상세 내용 펼치기
                driver.execute_script("arguments[0].click();", title_elem)
                time.sleep(0.2)

                desc = rows[i + 1].find_element(By.CSS_SELECTOR, "td").text.strip()

                all_subjects.append({
                    "grade_year": grade_year,
                    "name": name,
                    "description": desc
                })

                print(f"[✓] {name} / {grade_year}")

                i += 2

            except Exception as e:
                print("❌ 에러:", e)
                i += 1

        offset += 30
        if offset > 10000:
            break

    return all_subjects

# ============================================
# 4. SCE(반도체융합공학과) 기본 테이블 크롤러
#    ⭐ SCE도 동일하게 td[6]이 이수학년
# ============================================

def crawl_sce_table(url):
    print("\n=== SCE: 반도체융합공학과 크롤링 시작 ===")

    driver.get(url)
    time.sleep(1.3)

    subjects = []

    # 모든 tr 가져오기
    rows = driver.find_elements(By.CSS_SELECTOR, "table tbody tr")

    for row in rows:
        tds = row.find_elements(By.TAG_NAME, "td")
        if len(tds) < 7:
            continue

        code = tds[0].text.strip()
        name = tds[1].text.strip()
        credit = tds[2].text.strip()
        grade_year = tds[6].text.strip()   # ⭐ 정확한 이수학년 위치
        desc = ""                          # ⭐ SCE는 설명 자체가 없음

        subjects.append({
            "grade_year": grade_year,
            "name": name,
            "description": desc
        })

        print(f"[✓] {name} / {grade_year}")

    print(f"총 과목 수: {len(subjects)}개")
    return subjects



# ============================================
# 5. 전체 실행
# ============================================

result = {
    "성균관대학교": {
        "정보통신대학": {},
        "반도체융합공학과": []
    }
}

# ICE 3개 학과
for dept_name, code in ICE_DEPARTMENTS.items():
    print(f"\n========== {dept_name} ==========")
    curriculum_url = ICE_CURRICULUM_URL.format(code)
    subjects = crawl_offset_curriculum(curriculum_url)
    result["성균관대학교"]["정보통신대학"][dept_name] = subjects

# SCE
sce_subjects = crawl_sce_table(SCE_URL)
result["성균관대학교"]["반도체융합공학과"] = sce_subjects

# 저장
with open("skku_ice_sce_courses_last.json", "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=4)

print("\n🎉 정보통신대학 + SCE 크롤링 완료!")
driver.quit()
