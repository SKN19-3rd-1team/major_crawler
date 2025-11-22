#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pdfplumber
import re
import json
from pathlib import Path
from collections import defaultdict

PDF_PATH = "요람2025(0401) - 수정.pdf"
OUTPUT_JSON = "sogang_course_final.json"

# ------------------------------
# 학과별 코드 prefix & 단과대 매핑
# ------------------------------
MAJOR_CODE_MAP = {
    # 자연과학대학
    "수학과": ["MAT"],
    "물리학과": ["PHY"],
    "화학과": ["CHM"],
    "생명과학과": ["BIO"],

    # 공과대학
    "전자공학과": ["EEE"],
    "화공생명공학과": ["CBE"],
    "기계공학과": ["MEE", "MEC", "MECH"],
    "시스템반도체공학과": ["SSD", "EEE"],

    # 소프트웨어융합대학
    "컴퓨터공학과": ["CSE"],
    "인공지능학과": ["AIX", "AIE"],
}

COLLEGE_MAP = {
    "수학과": "자연과학대학",
    "물리학과": "자연과학대학",
    "화학과": "자연과학대학",
    "생명과학과": "자연과학대학",

    "전자공학과": "공과대학",
    "화공생명공학과": "공과대학",
    "기계공학과": "공과대학",
    "시스템반도체공학과": "공과대학",

    "컴퓨터공학과": "소프트웨어융합대학",
    "인공지능학과": "소프트웨어융합대학",
}

# 교양/공통 prefix (완전히 제외)
NON_MAJOR_PREFIXES = [
    "CHS", "CUL", "LCU", "LHE", "ECO", "ENG",
    "PHI", "THE", "HSS", "ART", "HUM", "INT",
    "KOR", "HIS", "COR", "CSW", "MAS", "STS", "EDU",
]

ALL_MAJOR_PREFIXES = {p for lst in MAJOR_CODE_MAP.values() for p in lst}

# "코드 + 과목명" 패턴 (줄 맨 앞)
CODE_NAME_RE = re.compile(r"^([A-Z]{3,4}\d{4})\s+(.+)$")
# 아무 코드 패턴 (설명 안에서 다른 과목 코드 찾을 때 사용)
ANY_CODE_RE = re.compile(r"[A-Z]{3,4}\d{4}")

# ------------------------------
# 페이지 내에서, i 이후에 "강의/실험 + 학점" 메타가 있는지 확인
# ------------------------------
def has_meta_nearby(lines, i, max_ahead=6):
    for j in range(i + 1, min(i + 1 + max_ahead, len(lines))):
        s = lines[j].strip()
        if ("강의" in s or "실험" in s) and "학점" in s:
            return True
    return False

# ------------------------------
# 코드+이름 라인 파싱 (엄격하게)
# ------------------------------
def parse_code_name_line(line: str):
    line = line.strip()
    m = CODE_NAME_RE.match(line)
    if not m:
        return None, None

    code = m.group(1)
    rest = m.group(2).strip()

    # 교양/공통 prefix 제거
    if any(code.startswith(p) for p in NON_MAJOR_PREFIXES):
        return None, None

    # 우리가 관리하는 전공 prefix가 아니면 제외
    if not any(code.startswith(p) for p in ALL_MAJOR_PREFIXES):
        return None, None

    # 줄 전체에 코드가 여러 개면 (예: "CHM1001 ..., CHM1002 ...") 헤더로 사용하지 않음
    if len(ANY_CODE_RE.findall(line)) > 1:
        return None, None

    # 과목명: 괄호로 시작하는 강의/학점 정보는 잘라냄
    name = rest.split("(강의")[0].split("(실험")[0].strip()
    if "  (" in name:
        name = name.split("  (")[0].strip()

    # name 안에 또 다른 코드가 있으면 (이상한 줄) 헤더로 사용하지 않음
    if ANY_CODE_RE.search(name):
        return None, None

    # 너무 짧으면 (이상한 경우) 버리기
    if len(name) < 2:
        return None, None

    return code, name

# ------------------------------
# 학년 추론 (코드 숫자 첫 자리)
# ------------------------------
def infer_grade_from_code(code: str):
    m = re.search(r"\d+", code)
    if not m:
        return None
    digits = m.group(0)
    if not digits:
        return None
    try:
        y = int(digits[0])
        if 1 <= y <= 4:
            return y
    except ValueError:
        pass
    return None

# ------------------------------
# 전기/전선 추론: 1-2학년 전기, 3-4학년 전선
# ------------------------------
def infer_classification_from_grade(grade: int | None):
    if grade is None:
        return None
    return "전기" if grade <= 2 else "전선"

# ------------------------------
# 메타/헤더/푸터 라인 판단
# ------------------------------
def is_meta_line(line: str) -> bool:
    s = line.strip()
    if not s:
        return True

    # 짧은 학점 정보
    if s.endswith("학점") and len(s) <= 5:
        return True

    # 강의/실험 시간
    if s.startswith("(") and ("강의" in s or "실험" in s):
        return True

    # 선수과목/동일과목/병행과목/수강대상 등
    meta_keywords = [
        "선수과목", "동일과목", "병행과목",
        "수강대상", "수강대상자",
    ]
    if any(s.startswith(k) for k in meta_keywords):
        return True

    # 페이지 헤더/푸터
    if "교육과정 ｜" in s:
        return True
    if "｜ 2025 서강대학교 요람" in s:
        return True

    # 이수표 테이블 헤더
    if "과목코드" in s and "교과목명" in s:
        return True

    return False

# ------------------------------
# 메인 파서
# ------------------------------
def extract_courses(pdf_path: str) -> dict:
    result = {"서강대": defaultdict(lambda: defaultdict(list))}
    seen_names = {major: set() for major in MAJOR_CODE_MAP.keys()}

    current_course = None  # {"code":..., "name":...}
    current_desc_lines: list[str] = []

    def flush_current_course():
        nonlocal current_course, current_desc_lines
        if not current_course:
            return

        code = current_course["code"]
        name = current_course["name"]

        # 메타 제외한 설명 줄만 모으기
        desc_candidates = []
        for l in current_desc_lines:
            if not is_meta_line(l):
                desc_candidates.append(l.strip())

        description = " ".join(desc_candidates).strip()

        # 설명이 하나도 없으면 (리스트/이수표) → 과목 자체를 버린다
        if not description:
            current_course = None
            current_desc_lines = []
            return

        # 설명 안에서 다른 prefix의 코드가 나오면 그 앞까지만 사용
        def trim_at_other_code(text: str) -> str:
            for m in ANY_CODE_RE.finditer(text):
                other_code = m.group(0)
                cur_prefix = code[:3]
                other_prefix = other_code[:3]
                if other_prefix != cur_prefix:
                    return text[:m.start()].rstrip()
            return text

        description = trim_at_other_code(description)

        # 너무 길면 잘라내기
        if len(description) > 700:
            description = description[:700].rstrip()

        if not description:
            current_course = None
            current_desc_lines = []
            return

        # 어느 학과에 넣을지 prefix로 결정
        for major, prefixes in MAJOR_CODE_MAP.items():
            if any(code.startswith(p) for p in prefixes):
                college = COLLEGE_MAP[major]

                if name in seen_names[major]:
                    break

                seen_names[major].add(name)

                grade = infer_grade_from_code(code)
                course_class = infer_classification_from_grade(grade)

                result["서강대"][college][major].append({
                    "name": name,
                    "grade": grade,
                    "course_classification": course_class,
                    "description": description,
                })
                break

        current_course = None
        current_desc_lines = []

    pdf_file = Path(pdf_path)
    with pdfplumber.open(pdf_file) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ""
            lines = text.splitlines()

            i = 0
            while i < len(lines):
                raw = lines[i]
                line = raw.rstrip("\n")

                # 페이지 헤더/푸터는 설명 경계 → 과목 flush
                if "교육과정 ｜" in line or "｜ 2025 서강대학교 요람" in line:
                    flush_current_course()
                    i += 1
                    continue

                # 1) 우선 "코드+이름" 후보인지 검사
                code, name = parse_code_name_line(line)
                if code and name and has_meta_nearby(lines, i):
                    # 이 줄을 진짜 교과목 헤더로 인정
                    flush_current_course()
                    current_course = {"code": code, "name": name}
                    current_desc_lines = []
                    i += 1
                    continue

                # 2) 현재 과목 설명 수집 중인 경우
                if current_course:
                    # 혹시 새로운 코드+이름이 보이면 (메타 근처 여부 상관없이)
                    # 지금 과목을 마무리하고 다음 루프로 넘긴다.
                    next_code, next_name = parse_code_name_line(line)
                    if next_code and next_name and has_meta_nearby(lines, i):
                        flush_current_course()
                        # 이번 줄은 다음 loop에서 헤더로 처리되도록 i를 줄이지 않고 계속 진행
                        continue

                    # 설명 후보로 추가
                    if line.strip():
                        current_desc_lines.append(line)
                        # 설명 줄 수가 너무 많으면 끊고 flush
                        if len(current_desc_lines) > 10:
                            flush_current_course()
                    i += 1
                    continue

                # 3) 현재 과목이 없으면 그냥 다음 줄로
                i += 1

    flush_current_course()

    # defaultdict -> dict
    result["서강대"] = {college: dict(majors) for college, majors in result["서강대"].items()}
    return result

# ------------------------------
# 실행부
# ------------------------------
def main():
    pdf_file = Path(PDF_PATH)
    if not pdf_file.exists():
        raise FileNotFoundError(f"{pdf_file} 파일을 찾을 수 없습니다. 같은 폴더에 두고 실행해 주세요.")

    data = extract_courses(str(pdf_file))

    with open(OUTPUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"완료! 결과 JSON → {OUTPUT_JSON}")

if __name__ == "__main__":
    main()
