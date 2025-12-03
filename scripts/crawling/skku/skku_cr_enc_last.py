from selenium import webdriver
from selenium.webdriver.common.by import By
import time, json
from bs4 import BeautifulSoup

# 🔥 각 학과별 curriculum URL 매핑
DEPTS = {
    "신소재공학부": "under_materials_curriculum.do",
    "기계공학부": "under_mechanical_curriculum.do",
    "건설환경공학부": "under_construction_curriculum.do",
    "시스템경영공학과": "under_system_curriculum.do",
    "건축학과(건축학계열)": "under_arch_curriculum.do",
    "나노공학과": "under_nano_curriculum.do",
    "양자정보공학과": "under_quantum_curriculum.do",
}

BASE = "https://enc.skku.edu/enc/{path}?pager.offset={offset}&lang=All"


def get_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--start-maximized")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_argument("--disable-gpu")
    return webdriver.Chrome(options=options)


def crawl_page(driver, url, dept_name):
    print(f"[접속] {url}")
    driver.get(url)
    time.sleep(1.5)

    soup = BeautifulSoup(driver.page_source, "html.parser")

    table = soup.select_one("table.skku-table.small.toggle")
    if not table:
        print("❌ 교육과정 테이블을 찾지 못함")
        return []

    rows = table.select("tbody > tr")
    results = []

    i = 0
    while i < len(rows):
        row = rows[i]
        tds = row.find_all("td")

        # 과목 행 판단
        if len(tds) >= 2 and tds[1].find("a"):
            code = tds[0].get_text(strip=True)
            subject = tds[1].get_text(strip=True)
            credit = tds[2].get_text(strip=True)
            year = tds[6].get_text(strip=True) if len(tds) > 6 else ""
            lang = tds[8].get_text(strip=True) if len(tds) > 8 else ""
            opened = tds[9].get_text(strip=True) if len(tds) > 9 else ""

            desc = ""
            # 다음 행이 설명행인지 확인
            if i + 1 < len(rows):
                next_row = rows[i + 1]
                if "dark" in (next_row.get("class") or []):
                    desc_td = next_row.find("td")
                    if desc_td:
                        desc = desc_td.get_text(" ", strip=True)

            results.append({
                "dept": dept_name,
                "code": code,
                "subject": subject,
                "credit": credit,
                "grade_year": year,  # ← ⭐ 이수학년 포함
                "lang": lang,
                "opened": opened,
                "description": desc,
            })

            i += 2
        else:
            i += 1

    # debug
    if results:
        print("  ├샘플:", results[0]["subject"], "/", results[0]["grade_year"])
    else:
        print("  └ 이 페이지에 과목 없음")

    return results


if __name__ == "__main__":
    driver = get_driver()
    final_data = []

    try:
        for dept_name, path in DEPTS.items():
            print(f"\n========== {dept_name} ==========")
            dept_results = []

            for offset in [0, 30, 60, 90, 120]:
                url = BASE.format(path=path, offset=offset)
                page_data = crawl_page(driver, url, dept_name)

                if not page_data:
                    break

                dept_results.extend(page_data)

            print(f"👉 {dept_name} 과목 수: {len(dept_results)}")
            final_data.extend(dept_results)

    finally:
        driver.quit()

    # JSON 저장
    with open("skku_enc_curriculum_all.json", "w", encoding="utf-8") as f:
        json.dump(final_data, f, ensure_ascii=False, indent=2)

    print("\n🎉 전체 학과 크롤링 완료!")


# ------------------------------------
# 🔄 JSON 구조 변환 (이수학년 포함)
# ------------------------------------

input_path = "skku_enc_curriculum_all.json"
output_path = "skku_enc_last.json"

with open(input_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# 구조 변환
result = {
    "성균관대학교": {
        "공과대학": {}
    }
}

# 학과별 분리
for item in data:
    dept = item["dept"]
    if dept not in result["성균관대학교"]["공과대학"]:
        result["성균관대학교"]["공과대학"][dept] = []

    result["성균관대학교"]["공과대학"][dept].append({
        "subject": item["subject"],
        "grade_year": item["grade_year"],  # ⭐ 추가됨
        "description": item["description"]
    })

with open(output_path, "w", encoding="utf-8") as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print("변환 완료:", output_path)
