import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from playwright.sync_api import Page, TimeoutError, sync_playwright

TARGET_SECTION_KEYWORD = "홍익"


def slugify(value: str) -> str:
    """Create a filesystem-friendly slug from a department name."""
    slug = re.sub(r"[^0-9a-zA-Z가-힣]+", "_", value)
    slug = slug.strip("_").lower()
    return slug or "unknown"


def parse_hongik_majors(
    readme_path: Path,
) -> Tuple[str, str, Dict[str, List[Dict[str, str]]]]:
    """
    Scan README.md and pull out the Hongik engineering college links.
    """
    lines = readme_path.read_text(encoding="utf-8").splitlines()
    majors: Dict[str, List[Dict[str, str]]] = {}
    current_college: Optional[str] = None
    target_section_name: Optional[str] = None
    base_url: Optional[str] = None

    for line in lines:
        stripped = line.strip()
        if stripped.startswith("#"):
            section_label = stripped.lstrip("#").strip()
            if TARGET_SECTION_KEYWORD in section_label:
                target_section_name = section_label
            else:
                if target_section_name:
                    break
                target_section_name = None
            current_college = None
            continue

        if not target_section_name:
            continue

        if not stripped.startswith("-"):
            continue

        indent = len(line) - len(line.lstrip(" "))
        text = stripped[1:].strip()

        if indent == 0 and "<" in text and ">" in text:
            url_match = re.search(r"<([^>]+)>", text)
            if url_match:
                url = url_match.group(1)
                base_url = url.split("{", 1)[0]
            continue

        if indent == 2:
            current_college = text
            majors.setdefault(current_college, [])
            continue

        if indent >= 4 and current_college and ":" in text:
            match = re.match(r"([^:]+):\s*(\?.+)", text)
            if match:
                dept_name = match.group(1).strip()
                query = match.group(2).strip()
                majors[current_college].append(
                    {"dept_name": dept_name, "query": query}
                )

    if not majors or not target_section_name or not base_url:
        raise ValueError("Failed to locate Hongik engineering majors in README.md")

    return target_section_name, base_url, majors


def extract_curriculum_items(page: Page) -> List[Dict[str, str]]:
    """
    Collect the curriculum title and description from the curriculum-box.
    """
    items: List[Dict[str, str]] = []
    rows = page.locator("div.curriculum-box li.grid-item")
    total = rows.count()
    for index in range(total):
        node = rows.nth(index)
        title = (node.locator("p.curriculum-title").text_content() or "").strip()
        desc_spans = node.locator("div.curriculum-desc.accordion-box span")
        span_count = desc_spans.count()
        description_parts = []
        for span_index in range(span_count):
            text = desc_spans.nth(span_index).text_content()
            if text:
                part = text.strip()
                if part:
                    description_parts.append(part)
        description = "\n".join(description_parts)
        if not title and not description:
            continue
        items.append({"name": title, "description": description})
    return items


def fetch_curriculum_for_query(
    page: Page, base_url: str, query: str
) -> List[Dict[str, str]]:
    """Load the department page and return collected curriculum entries."""
    url = f"{base_url}{query}"
    print(f"[INFO] Crawling {url}")
    page.goto(url, wait_until="networkidle")
    try:
        page.wait_for_selector("div.curriculum-box", timeout=10_000)
    except TimeoutError:
        return []
    return extract_curriculum_items(page)


def crawl_hongik_majors(
    univ_name: str, base_url: str, majors_by_college: Dict[str, List[Dict[str, str]]]
) -> Dict[str, Dict[str, Dict[str, List[Dict[str, str]]]]]:
    """Visit each department page and grab their curricula."""
    data: Dict[str, Dict[str, Dict[str, List[Dict[str, str]]]]] = {
        univ_name: {}
    }
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=False, slow_mo=100)
        page = browser.new_page()
        page.set_default_timeout(15_000)

        for college_name, entries in majors_by_college.items():
            college_group = data[univ_name].setdefault(college_name, {})
            for entry in entries:
                dept_name = entry["dept_name"]
                courses = fetch_curriculum_for_query(page, base_url, entry["query"])
                college_group[dept_name] = courses

        browser.close()

    return data


def save_department_output(
    out_dir: Path,
    univ_name: str,
    college_name: str,
    dept_name: str,
    query: str,
    courses: List[Dict[str, str]],
) -> Path:
    slug = slugify(f"{dept_name}_{query}")
    out_path = out_dir / f"hongik_{slug}.json"
    payload = {univ_name: {college_name: {dept_name: courses}}}
    out_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[INFO] Saved {out_path}")
    return out_path


def save_aggregated_output(out_dir: Path, univ_name: str, data: Dict) -> Path:
    slug = slugify(univ_name)
    out_path = out_dir / f"hongik_all_{slug}.json"
    out_path.write_text(
        json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(f"[INFO] Aggregated output: {out_path}")
    return out_path


def main():
    readme_path = Path("README.md")
    univ_name, base_url, majors_by_college = parse_hongik_majors(readme_path)
    data = crawl_hongik_majors(univ_name, base_url, majors_by_college)

    out_dir = Path("major_crawler_output")
    out_dir.mkdir(exist_ok=True)

    for college_name, entries in majors_by_college.items():
        for entry in entries:
            dept_name = entry["dept_name"]
            query = entry["query"]
            courses = (
                data[univ_name]
                .get(college_name, {})
                .get(dept_name, [])
            )
            save_department_output(
                out_dir, univ_name, college_name, dept_name, query, courses
            )

    save_aggregated_output(out_dir, univ_name, data)


if __name__ == "__main__":
    main()
