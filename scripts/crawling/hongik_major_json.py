from pathlib import Path
from bs4 import BeautifulSoup
import json

def parse_hongik_html(html_path: Path):
    """hongik_*.html 하나를 파싱해서 과목 리스트를 반환"""
    html_text = html_path.read_text(encoding="utf-8")
    soup = BeautifulSoup(html_text, "html.parser")

    courses = []

    # 파일 구조에 맞게 태그 선택 (이전 답변과 동일한 로직)
    for item in soup.select("div.curriculum-box li.grid-item"):
        title_box = item.select_one("div.curriculum-title-box")
        if not title_box:
            continue

        # 과목명
        title_tag = title_box.select_one("p.curriculum-title")
        title = title_tag.get_text(strip=True) if title_tag else ""

        # 학년/학기
        li_tags = title_box.select(".curriculum-sub-title ul li")
        li_texts = [li.get_text(strip=True) for li in li_tags]

        grade_semester = li_texts[0] if len(li_texts) > 0 else None   # 예: "2학년/1학기"
        try:
            year_part, sem_part = grade_semester.split("/")
            year = year_part.replace("학년", "").strip()
            sem = sem_part.replace("학기", "").strip()
            grade_semester = f"{year}-{sem}"     # 예: "3-1"
        except ValueError:
            grade_semester = grade_semester  # 혹시 형식 다르면 원문 유지
        
        # 전공 필수/ 전공 선택
        category       = li_texts[1] if len(li_texts) > 1 else None   # 예: "전공필수"

        # 과목 설명
        desc_span = title_box.select_one(".curriculum-desc span")
        description = desc_span.get_text(" ", strip=True) if desc_span else ""

        courses.append({
            "name": title,
            "grade_semester": grade_semester,
            "category": category,
            "description": description,
        })

    return courses


def main():
    # html 파일들이 있는 디렉터리 (스크립트와 같은 폴더면 ".")
    base_dir = Path("data/hongik")  # 필요하면 Path("path/to/dir") 로 바꿔도 됨

    # hongik_로 시작하고 .html로 끝나는 파일들 전부 순회
    html_files = sorted(base_dir.glob("hongik_*.html"))

    if not html_files:
        print("hongik_*.html 파일을 찾지 못했습니다.")
        return

    for html_path in html_files:
        print(f"처리 중: {html_path.name}")
        courses = parse_hongik_html(html_path)

        # 같은 이름의 json 파일로 저장 (확장자만 .json 으로 변경)
        out_path = html_path.with_suffix(".json")
        with out_path.open("w", encoding="utf-8") as f:
            json.dump(courses, f, ensure_ascii=False, indent=2)

        print(f"  → {len(courses)}개 과목을 {out_path.name} 에 저장 완료")

    print("모든 파일 변환 완료!")


if __name__ == "__main__":
    main()
