import time, json
from selenium import webdriver
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service

BASE_URL = "https://registrar.korea.ac.kr/eduinfo/info/registration_courses.do"
CHROME_DRIVER_PATH = r"C:\SKN_19\SKN19-3RD_1TEAM\chromedriver.exe"

UNIVERSITY = "고려대학교"
YEAR = "2025"
TERMS = ["1R", "2R"]
COLLEGES = ["이과대학", "공과대학", "정보대학"]


def switch_to_frame(driver):
    driver.switch_to.default_content()
    frames = driver.find_elements(By.TAG_NAME, "iframe")
    for fr in frames:
        try:
            driver.switch_to.default_content()
            driver.switch_to.frame(fr)
            driver.find_element(By.ID, "pCol")
            return True
        except:
            continue
    return False


def read_popup(driver, wait):
    """팝업에서 과목명 / 강의요목 / 연도-학기 / 학수번호-분반 크롤링"""

    time.sleep(1.0)

    for _ in range(10):
        try:
            # 과목명
            name = driver.find_element(
                By.XPATH, "//th[text()='과목명']/following-sibling::td"
            ).text.strip()

            # 강의요목
            desc = driver.find_element(
                By.XPATH, "//th[text()='강의요목']/following-sibling::td"
            ).text.strip()

            # 연도-학기   (팝업 상단)
            year_term = driver.find_element(
                By.XPATH, "//th[contains(text(),'연도')]/following-sibling::td"
            ).text.strip()

            # 학수번호 - 분반
            course_code = driver.find_element(
                By.XPATH, "//th[contains(text(),'학수번호')]/following-sibling::td"
            ).text.strip()

            # 모든 값이 채워졌는지 확인
            if name and desc and year_term and course_code:
                return name, desc, year_term, course_code

            time.sleep(0.5)

        except:
            time.sleep(0.5)

    # 실패 시 빈 값 반환
    return "", "", "", ""



def crawl():
    data = {UNIVERSITY: {}}

    options = webdriver.ChromeOptions()
    options.add_argument("--window-size=1500,1200")
    options.add_argument("--disable-popup-blocking")

    driver = webdriver.Chrome(service=Service(CHROME_DRIVER_PATH), options=options)
    wait = WebDriverWait(driver, 10)

    main_handle = driver.current_window_handle

    for term in TERMS:

        print(f"\n\n======================== [{term}] 시작 ========================")

        # 매 학기마다 페이지 다시 로드 — 중요!!
        driver.get(BASE_URL)
        time.sleep(2)

        if not switch_to_frame(driver):
            print("[ERROR] iframe 진입 실패")
            continue

        # 연도/학기 설정
        try: Select(driver.find_element(By.ID, "pYear")).select_by_visible_text(YEAR)
        except: pass

        try: Select(driver.find_element(By.ID, "pTerm")).select_by_value(term)
        except: pass

        for college in COLLEGES:
            print(f"\n========== {college} ==========")

            data[UNIVERSITY].setdefault(college, {})

            # 단과대 선택
            Select(driver.find_element(By.ID, "pCol")).select_by_visible_text(college)
            time.sleep(1)

            # 학과 리스트를 매번 fresh하게 가져와야 한다
            dept_sel = Select(driver.find_element(By.ID, "pDept"))
            dept_values = [
                opt.get_attribute("value")
                for opt in dept_sel.options
                if opt.get_attribute("value").strip()
            ]

            for dept_val in dept_values:

                # iframe 재진입 + dept selector 다시 가져오기
                if not switch_to_frame(driver):
                    continue

                dept_sel = Select(driver.find_element(By.ID, "pDept"))
                dept_sel.select_by_value(dept_val)
                dept_name = dept_sel.first_selected_option.text.strip()

                if dept_name == college:
                    print(f"--- {dept_name} (스킵) ---")
                    continue

                print(f"\n--- {dept_name} ---")

                data[UNIVERSITY][college].setdefault(dept_name, [])

                # 조회
                driver.find_element(By.ID, "btnSearch").click()

                try:
                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
                except:
                    print("  [WARN] 조회 실패")
                    continue

                time.sleep(0.5)

                # span 목록을 html 기반으로 다시 파싱해야 안정적
                spans = driver.find_elements(By.XPATH, "//span[contains(@onclick,'fnPlanView')]")
                total = len(spans)
                print(f"  [INFO] {total}개 과목")

                for idx in range(total):

                    # iframe 재진입
                    if not switch_to_frame(driver):
                        break

                    wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "table tbody tr")))
                    spans = driver.find_elements(By.XPATH, "//span[contains(@onclick,'fnPlanView')]")

                    if idx >= len(spans):
                        break

                    span = spans[idx]

                    # 팝업 열기
                    before = driver.window_handles[:]
                    driver.execute_script("arguments[0].click();", span)

                    popup = None
                    for _ in range(15):
                        after = driver.window_handles
                        if len(after) > len(before):
                            popup = [h for h in after if h not in before][0]
                            break
                        time.sleep(0.2)

                    if not popup:
                        print("    [ERROR] 팝업 없음 → skip")
                        continue

                    # 팝업 이동
                    driver.switch_to.window(popup)

                    name, desc, year_term, course_code = read_popup(driver, wait)

                    print(f"    → {name}")

                    data[UNIVERSITY][college][dept_name].append({
                        "name": name,
                        "description": desc,
                        "year_term": year_term,
                        "course_code": course_code
                    })

                    # 팝업 닫기
                    try:
                        close_btn = driver.find_element(By.CLASS_NAME, "close")
                        driver.execute_script("arguments[0].click();", close_btn)
                    except:
                        try:
                            driver.close()
                        except:
                            pass

                    driver.switch_to.window(main_handle)
                    # 다시 iframe 복귀
                    switch_to_frame(driver)

    # 저장
    with open("korea_2025_courses.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print("\n🎉 전체 크롤링 완료!")
    driver.quit()


if __name__ == "__main__":
    crawl()
