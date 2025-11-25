import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from playwright.sync_api import Page, sync_playwright

BASE_URL = "https://www.konkuk.ac.kr/bulletins25/{major_id}/subview.do"
TARGET_UNIV_KEYWORD = "건국"

def slugify(value: str) -> str:
    """Create a filename-friendly slug from input text."""
    slug = re.sub(r"[^0-9a-zA-Z가-힣]+", "_", value)
    slug = slug.strip("_").lower()
    return slug or "unknown"


def parse_konkuk_majors(readme_path: Path) -> Tuple[str, Dict[str, List[Dict[str, str]]]]:
    """
    Scan README.md and build a map of colleges -> department metadata for KonKuk.
    """
    lines = readme_path.read_text(encoding="utf-8").splitlines()
    majors: Dict[str, List[Dict[str, str]]] = {}
    current_college: Optional[str] = None
    target_section_name: Optional[str] = None
    in_target_section = False

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("##"):
            section_label = stripped.lstrip("#").strip()
            in_target_section = TARGET_UNIV_KEYWORD in section_label
            if in_target_section:
                target_section_name = section_label
            current_college = None
            continue

        if not in_target_section or not stripped.startswith("-"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        text = stripped[1:].strip()

        if indent == 2:
            current_college = text
            majors.setdefault(current_college, [])
            continue

        if indent >= 4 and current_college:
            match = re.match(r"(.+?):\s*(\d+)\b", text)
            if match:
                dept_name = match.group(1).strip()
                major_id = match.group(2).strip()
                majors[current_college].append(
                    {"dept_name": dept_name, "major_id": major_id}
                )

    if not majors or not target_section_name:
        raise ValueError("No KonKuk majors were found in README.md")

    return target_section_name, majors


def parse_korean_desc_from_onclick(onclick_attr: str) -> str:
    """
    Extract the Korean description from jf_view(`...`, `...`).
    """
    if not onclick_attr:
        return ""

    parts = onclick_attr.split("`")
    if len(parts) >= 3:
        return parts[1].strip()
    return ""


def extract_courses_from_table(page: Page) -> List[Dict]:
    """
    Extract Korea course data from the standard list table.
    """
    rows = page.locator("table tbody tr")
    row_count = rows.count()

    courses: List[Dict] = []

    for i in range(row_count):
        row = rows.nth(i)
        tds = row.locator("td")

        if tds.count() < 5:
            continue
        
        # 학년-학기
        grade_semester = tds.nth(0).inner_text().strip()
        # 이수구분 (전선, 전필)
        course_classification = tds.nth(1).inner_text().strip()
        # 교과목명
        name_cell = tds.nth(3)
        name_kor = name_cell.inner_text().strip()
        # 영문 교과목명
        name_eng = tds.nth(4).inner_text().strip()

        if not name_kor:
            continue

        description = ""
        link = name_cell.locator("a")
        if link.count() > 0:
            onclick_attr = link.first.get_attribute("onclick") or ""
            description = parse_korean_desc_from_onclick(onclick_attr)

        course = {
            "grade_semester": grade_semester,
            "course_classification": course_classification,
            "name": name_kor,
            "name_en": name_eng,
            "description": description,
        }
        courses.append(course)

    return courses


def fetch_major_courses(page: Page, major_id: str) -> List[Dict]:
    """
    Navigate to the major page and extract courses.
    """
    url = BASE_URL.format(major_id=major_id)
    print(f"[INFO] Crawling {url}")
    page.goto(url, wait_until="domcontentloaded", timeout=60000)
    page.wait_for_load_state("networkidle")
    return extract_courses_from_table(page)


def crawl_konkuk_majors(
    univ_name: str, majors_by_college: Dict[str, List[Dict[str, str]]]
) -> Dict[str, Dict[str, List[Dict]]]:
    data: Dict[str, Dict[str, List[Dict]]] = {univ_name: {}}

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()
        page.set_default_timeout(10_000)

        for college_name, entries in majors_by_college.items():
            college_group = data[univ_name].setdefault(college_name, {})
            for entry in entries:
                courses = fetch_major_courses(page, entry["major_id"])
                college_group[entry["dept_name"]] = courses

        browser.close()

    return data


def save_department_output(
    out_dir: Path,
    univ_name: str,
    college_name: str,
    dept_name: str,
    major_id: str,
    courses: List[Dict],
) -> Path:
    slug = slugify(dept_name)
    out_path = out_dir / f"konkuk_{slug}.json"
    payload = {univ_name: {college_name: {dept_name: courses}}}
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[INFO] Saved {out_path}")
    return out_path


def save_aggregated_output(out_dir: Path, univ_name: str, data: Dict) -> Path:
    slug = slugify(univ_name)
    out_path = out_dir / f"konkuk_all_{slug}.json"
    out_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[INFO] Aggregated output: {out_path}")
    return out_path


def main():
    readme_path = Path("README.md")
    univ_name, majors_by_college = parse_konkuk_majors(readme_path)
    data = crawl_konkuk_majors(univ_name, majors_by_college)

    out_dir = Path("data/konkuk")
    out_dir.mkdir(exist_ok=True)

    for college_name, entries in majors_by_college.items():
        for entry in entries:
            dept_name = entry["dept_name"]
            major_id = entry["major_id"]
            courses = (
                data[univ_name]
                .get(college_name, {})
                .get(dept_name, [])
            )
            save_department_output(
                out_dir, univ_name, college_name, dept_name, major_id, courses
            )

    save_aggregated_output(out_dir, univ_name, data)


if __name__ == "__main__":
    main()
