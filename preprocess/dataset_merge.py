"""
데이터셋 병합 스크립트

data/ 디렉토리 이하의 모든 대학 JSON 파일들을 하나로 병합합니다.
- 건국대(konkuk): 각 학과별 JSON 파일들을 병합
- 홍익대(hongik): 각 학과별 JSON 파일들을 병합 (category → course_classification 변환)
- 성균관대(sungkyunkwan): grade_year → grade_semester 변환, course_classification 필드 추가
- 한양대(hanyang), 서울대(seoul), 이화여대(ewha): 표준 포맷 JSON 파일들 병합
- 기타 대학들(부산대, 충북대, 강원대, 경북대, 경상대, 제주대, 전북대): 표준 포맷 JSON 파일들 병합
- 고려대(korea): year_term → grade_semester 변환, course_code → 학수번호 변환
- 서강대(seogang): grade → grade_semester 변환 (course_classification에서 학기 추정)
"""

import json
from pathlib import Path
from typing import Dict, List, Any


def load_json_file(file_path: Path) -> Any:
    """JSON 파일을 로드합니다."""
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)


def merge_hongik_data(data_dir: Path) -> Dict:
    """
    홍익대 JSON 파일들을 병합합니다.

    홍익대는 각 파일이 배열 형태로 되어 있고, 파일명에 학과명이 포함되어 있습니다.
    예: hongik_컴퓨터공학.json -> "컴퓨터공학"
    배열 포맷을 표준 포맷으로 변환하며, category를 course_classification으로 변환합니다.
    """
    hongik_dir = data_dir / "hongik"
    if not hongik_dir.exists():
        print(f"경고: {hongik_dir} 폴더를 찾을 수 없습니다.")
        return {}

    hongik_data = {"홍익대학교": {"공과대학": {}}}

    for json_file in sorted(hongik_dir.glob("hongik_*.json")):
        # 파일명에서 학과명 추출: hongik_컴퓨터공학.json -> 컴퓨터공학
        dept_name = json_file.stem.replace("hongik_", "")

        courses = load_json_file(json_file)

        # category를 course_classification으로 변환
        for course in courses:
            if "category" in course:
                course["course_classification"] = course.pop("category")

        hongik_data["홍익대학교"]["공과대학"][dept_name] = courses
        print(f"[OK] 홍익대 - {dept_name}: {len(courses)}개 과목")

    return hongik_data


def merge_konkuk_data(data_dir: Path) -> Dict:
    """
    건국대 JSON 파일들을 병합합니다.

    건국대는 각 학과별로 별도 JSON 파일이 있으며, 모두 표준 포맷을 따릅니다.
    예: konkuk_컴퓨터공학부.json -> {"건국대": {"공과대학": {"컴퓨터공학부": [...]}}}
    """
    konkuk_dir = data_dir / "konkuk"
    if not konkuk_dir.exists():
        print(f"경고: {konkuk_dir} 폴더를 찾을 수 없습니다.")
        return {}

    # 통합 파일이 있으면 제외
    json_files = [f for f in konkuk_dir.glob("konkuk_*.json") if "all" not in f.stem.lower()]

    if not json_files:
        print(f"경고: {konkuk_dir}에 JSON 파일이 없습니다.")
        return {}

    merged_data = {}

    for json_file in sorted(json_files):
        file_data = load_json_file(json_file)

        # 각 파일의 데이터를 병합
        for univ_name, colleges in file_data.items():
            if univ_name not in merged_data:
                merged_data[univ_name] = {}

            for college_name, departments in colleges.items():
                if college_name not in merged_data[univ_name]:
                    merged_data[univ_name][college_name] = {}

                for dept_name, courses in departments.items():
                    if dept_name in merged_data[univ_name][college_name]:
                        # 중복된 학과가 있으면 과목을 추가
                        merged_data[univ_name][college_name][dept_name].extend(courses)
                        print(f"[OK] {univ_name} - {college_name} - {dept_name}: {len(courses)}개 과목 추가 (누적)")
                    else:
                        merged_data[univ_name][college_name][dept_name] = courses
                        print(f"[OK] {univ_name} - {college_name} - {dept_name}: {len(courses)}개 과목")

    return merged_data


def merge_sungkyunkwan_data(data_dir: Path) -> Dict:
    """
    성균관대 JSON 파일을 병합합니다.

    성균관대는 표준 스키마를 따르지만, 필드명이 다릅니다:
    - grade_year -> grade_semester로 변환
    - course_classification 필드가 없으므로 빈 문자열로 추가

    주의: 일부 단과대학은 dict 형태, 일부는 list 형태로 되어있음
    """
    skku_dir = data_dir / "sungkyunkwan"
    if not skku_dir.exists():
        print(f"경고: {skku_dir} 폴더를 찾을 수 없습니다.")
        return {}

    merged_data = {}

    json_files = list(skku_dir.glob("*.json"))
    if not json_files:
        print(f"경고: {skku_dir}에 JSON 파일이 없습니다.")
        return {}

    for json_file in sorted(json_files):
        file_data = load_json_file(json_file)

        # 각 파일의 데이터를 병합
        for univ_name, colleges in file_data.items():
            if univ_name not in merged_data:
                merged_data[univ_name] = {}

            for college_name, departments in colleges.items():
                if college_name not in merged_data[univ_name]:
                    merged_data[univ_name][college_name] = {}

                # departments가 list인 경우 (단과대학 자체가 과목 리스트)
                if isinstance(departments, list):
                    # 필드명 변환
                    for course in departments:
                        if "grade_year" in course:
                            course["grade_semester"] = course.pop("grade_year")
                        if "course_classification" not in course:
                            course["course_classification"] = ""

                    # 단과대학명을 학과명으로 사용
                    merged_data[univ_name][college_name][college_name] = departments
                    print(f"[OK] {univ_name} - {college_name} - {college_name}: {len(departments)}개 과목")

                # departments가 dict인 경우 (정상적인 학과별 구조)
                elif isinstance(departments, dict):
                    for dept_name, courses in departments.items():
                        # 필드명 변환
                        for course in courses:
                            if "grade_year" in course:
                                course["grade_semester"] = course.pop("grade_year")
                            if "course_classification" not in course:
                                course["course_classification"] = ""

                        if dept_name in merged_data[univ_name][college_name]:
                            # 중복된 학과가 있으면 과목을 추가
                            merged_data[univ_name][college_name][dept_name].extend(courses)
                            print(f"[OK] {univ_name} - {college_name} - {dept_name}: {len(courses)}개 과목 추가 (누적)")
                        else:
                            merged_data[univ_name][college_name][dept_name] = courses
                            print(f"[OK] {univ_name} - {college_name} - {dept_name}: {len(courses)}개 과목")

    return merged_data


def merge_korea_data(data_dir: Path) -> Dict:
    """
    고려대 JSON 파일을 병합합니다.

    고려대는 표준 스키마를 따르지만, 필드명이 다릅니다:
    - year_term → grade_semester로 변환 (예: "2025 - 1학기" → "1-1")
    - course_code → 학수번호로 변환
    - course_classification 필드가 없으므로 빈 문자열로 추가
    """
    korea_dir = data_dir / "korea"
    if not korea_dir.exists():
        print(f"경고: {korea_dir} 폴더를 찾을 수 없습니다.")
        return {}

    merged_data = {}

    json_files = list(korea_dir.glob("*.json"))
    if not json_files:
        print(f"경고: {korea_dir}에 JSON 파일이 없습니다.")
        return {}

    for json_file in sorted(json_files):
        file_data = load_json_file(json_file)

        # 각 파일의 데이터를 병합
        for univ_name, colleges in file_data.items():
            if univ_name not in merged_data:
                merged_data[univ_name] = {}

            for college_name, departments in colleges.items():
                if college_name not in merged_data[univ_name]:
                    merged_data[univ_name][college_name] = {}

                for dept_name, courses in departments.items():
                    # 필드명 변환
                    for course in courses:
                        # year_term을 grade_semester로 변환 (예: "2025 - 1학기" → "1-1")
                        if "year_term" in course:
                            year_term = course.pop("year_term")
                            # "2025 - 1학기" 형식에서 학기 정보 추출
                            if "1학기" in year_term:
                                course["grade_semester"] = "1-1"
                            elif "2학기" in year_term:
                                course["grade_semester"] = "1-2"
                            else:
                                course["grade_semester"] = ""

                        # course_code를 학수번호로 변환
                        if "course_code" in course:
                            course["학수번호"] = course.pop("course_code")

                        # course_classification 필드 추가
                        if "course_classification" not in course:
                            course["course_classification"] = ""

                    if dept_name in merged_data[univ_name][college_name]:
                        # 중복된 학과가 있으면 과목을 추가
                        merged_data[univ_name][college_name][dept_name].extend(courses)
                        print(f"[OK] {univ_name} - {college_name} - {dept_name}: {len(courses)}개 과목 추가 (누적)")
                    else:
                        merged_data[univ_name][college_name][dept_name] = courses
                        print(f"[OK] {univ_name} - {college_name} - {dept_name}: {len(courses)}개 과목")

    return merged_data


def merge_seogang_data(data_dir: Path) -> Dict:
    """
    서강대 JSON 파일을 병합합니다.

    서강대는 표준 스키마를 따르지만, 필드가 다릅니다:
    - grade → grade_semester로 변환 (예: 2 → "2-1" 또는 "2-2", course_classification에서 추정)
    - 학수번호 필드가 없으므로 빈 문자열로 추가
    """
    seogang_dir = data_dir / "seogang"
    if not seogang_dir.exists():
        print(f"경고: {seogang_dir} 폴더를 찾을 수 없습니다.")
        return {}

    merged_data = {}

    json_files = list(seogang_dir.glob("*.json"))
    if not json_files:
        print(f"경고: {seogang_dir}에 JSON 파일이 없습니다.")
        return {}

    for json_file in sorted(json_files):
        file_data = load_json_file(json_file)

        # 각 파일의 데이터를 병합
        for univ_name, colleges in file_data.items():
            if univ_name not in merged_data:
                merged_data[univ_name] = {}

            for college_name, departments in colleges.items():
                if college_name not in merged_data[univ_name]:
                    merged_data[univ_name][college_name] = {}

                for dept_name, courses in departments.items():
                    # 필드명 변환
                    for course in courses:
                        # grade를 grade_semester로 변환
                        if "grade" in course:
                            grade = course.pop("grade")
                            # course_classification에서 학기 정보 추정 ("전기" = 1학기, "후기" = 2학기)
                            classification = course.get("course_classification", "")
                            semester = "1" if "전기" in classification else "2" if "후기" in classification else "1"
                            course["grade_semester"] = f"{grade}-{semester}"

                        # 학수번호 필드 추가
                        if "학수번호" not in course:
                            course["학수번호"] = ""

                    if dept_name in merged_data[univ_name][college_name]:
                        # 중복된 학과가 있으면 과목을 추가
                        merged_data[univ_name][college_name][dept_name].extend(courses)
                        print(f"[OK] {univ_name} - {college_name} - {dept_name}: {len(courses)}개 과목 추가 (누적)")
                    else:
                        merged_data[univ_name][college_name][dept_name] = courses
                        print(f"[OK] {univ_name} - {college_name} - {dept_name}: {len(courses)}개 과목")

    return merged_data


def merge_standard_format_data(data_dir: Path, univ_folder: str) -> Dict:
    """
    표준 포맷을 따르는 대학 데이터를 병합합니다.

    한양대, 서울대, 이화여대는 이미 표준 스키마를 따릅니다:
    {"대학명": {"단과대학": {"학과명": [...]}}}
    """
    univ_dir = data_dir / univ_folder
    if not univ_dir.exists():
        print(f"경고: {univ_dir} 폴더를 찾을 수 없습니다.")
        return {}

    merged_data = {}

    json_files = list(univ_dir.glob("*.json"))
    if not json_files:
        print(f"경고: {univ_dir}에 JSON 파일이 없습니다.")
        return {}

    for json_file in sorted(json_files):
        file_data = load_json_file(json_file)

        # 각 파일의 데이터를 병합
        for univ_name, colleges in file_data.items():
            if univ_name not in merged_data:
                merged_data[univ_name] = {}

            for college_name, departments in colleges.items():
                if college_name not in merged_data[univ_name]:
                    merged_data[univ_name][college_name] = {}

                for dept_name, courses in departments.items():
                    if dept_name in merged_data[univ_name][college_name]:
                        # 중복된 학과가 있으면 과목을 추가
                        merged_data[univ_name][college_name][dept_name].extend(courses)
                        print(f"[OK] {univ_name} - {college_name} - {dept_name}: {len(courses)}개 과목 추가 (누적)")
                    else:
                        merged_data[univ_name][college_name][dept_name] = courses
                        print(f"[OK] {univ_name} - {college_name} - {dept_name}: {len(courses)}개 과목")

    return merged_data


def deep_merge_dicts(dict1: Dict, dict2: Dict) -> Dict:
    """
    두 딕셔너리를 깊게 병합합니다.
    dict2의 내용을 dict1에 병합하되, 중복된 키는 dict2의 값을 사용합니다.
    """
    result = dict1.copy()

    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = deep_merge_dicts(result[key], value)
        else:
            result[key] = value

    return result


def merge_all_universities(data_dir: Path, output_path: Path):
    """
    모든 대학의 데이터를 병합하여 하나의 JSON 파일로 저장합니다.
    """
    print("=" * 60)
    print("데이터셋 병합 시작")
    print("=" * 60)

    all_data = {}

    # 1. 건국대 데이터 병합
    print("\n[1] 건국대학교 데이터 처리 중...")
    konkuk_data = merge_konkuk_data(data_dir)
    all_data = deep_merge_dicts(all_data, konkuk_data)

    # 2. 홍익대 데이터 병합
    print("\n[2] 홍익대학교 데이터 처리 중...")
    hongik_data = merge_hongik_data(data_dir)
    all_data = deep_merge_dicts(all_data, hongik_data)

    # 3. 성균관대 데이터 병합
    print("\n[3] 성균관대학교 데이터 처리 중...")
    skku_data = merge_sungkyunkwan_data(data_dir)
    all_data = deep_merge_dicts(all_data, skku_data)

    # 4. 한양대 데이터 병합
    print("\n[4] 한양대학교 데이터 처리 중...")
    hanyang_data = merge_standard_format_data(data_dir, "hanyang")
    all_data = deep_merge_dicts(all_data, hanyang_data)

    # 5. 서울대 데이터 병합
    print("\n[5] 서울대학교 데이터 처리 중...")
    seoul_data = merge_standard_format_data(data_dir, "seoul")
    all_data = deep_merge_dicts(all_data, seoul_data)

    # 6. 이화여대 데이터 병합
    print("\n[6] 이화여자대학교 데이터 처리 중...")
    ewha_data = merge_standard_format_data(data_dir, "ewha")
    all_data = deep_merge_dicts(all_data, ewha_data)

    # 7. 부산대 데이터 병합
    print("\n[7] 부산대학교 데이터 처리 중...")
    busan_data = merge_standard_format_data(data_dir, "busan")
    all_data = deep_merge_dicts(all_data, busan_data)

    # 8. 충북대 데이터 병합
    print("\n[8] 충북대학교 데이터 처리 중...")
    chungbook_data = merge_standard_format_data(data_dir, "chungbook")
    all_data = deep_merge_dicts(all_data, chungbook_data)

    # 9. 강원대 데이터 병합
    print("\n[9] 강원대학교 데이터 처리 중...")
    gangwon_data = merge_standard_format_data(data_dir, "gangwon")
    all_data = deep_merge_dicts(all_data, gangwon_data)

    # 10. 경북대 데이터 병합
    print("\n[10] 경북대학교 데이터 처리 중...")
    gyungbook_data = merge_standard_format_data(data_dir, "gyungbook")
    all_data = deep_merge_dicts(all_data, gyungbook_data)

    # 11. 경상대 데이터 병합
    print("\n[11] 경상대학교 데이터 처리 중...")
    gyungsang_data = merge_standard_format_data(data_dir, "gyungsang")
    all_data = deep_merge_dicts(all_data, gyungsang_data)

    # 12. 제주대 데이터 병합
    print("\n[12] 제주대학교 데이터 처리 중...")
    jeju_data = merge_standard_format_data(data_dir, "jeju")
    all_data = deep_merge_dicts(all_data, jeju_data)

    # 13. 전북대 데이터 병합
    print("\n[13] 전북대학교 데이터 처리 중...")
    junbook_data = merge_standard_format_data(data_dir, "junbook")
    all_data = deep_merge_dicts(all_data, junbook_data)

    # 14. 고려대 데이터 병합
    print("\n[14] 고려대학교 데이터 처리 중...")
    korea_data = merge_korea_data(data_dir)
    all_data = deep_merge_dicts(all_data, korea_data)

    # 15. 서강대 데이터 병합
    print("\n[15] 서강대학교 데이터 처리 중...")
    seogang_data = merge_seogang_data(data_dir)
    all_data = deep_merge_dicts(all_data, seogang_data)

    # 16. 통합 데이터 저장
    print("\n" + "=" * 60)
    print("통합 데이터 저장 중...")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] 저장 완료: {output_path}")

    # 17. 통계 출력
    print("\n" + "=" * 60)
    print("병합 완료 통계:")
    print("=" * 60)

    for univ_name, colleges in all_data.items():
        total_courses = 0
        dept_count = 0

        for college_name, departments in colleges.items():
            dept_count += len(departments)
            for dept_name, courses in departments.items():
                total_courses += len(courses)

        print(f"{univ_name}: {dept_count}개 학과, {total_courses}개 과목")

    total_universities = len(all_data)
    print(f"\n총 {total_universities}개 대학 데이터 병합 완료")
    print("=" * 60)


def main():
    """메인 함수"""
    # 프로젝트 루트 디렉터리 (preprocess 폴더의 부모)
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    output_path = project_root / "data/merged_university_courses.json"

    if not data_dir.exists():
        print(f"오류: {data_dir} 폴더를 찾을 수 없습니다.")
        return

    merge_all_universities(data_dir, output_path)


if __name__ == "__main__":
    main()
