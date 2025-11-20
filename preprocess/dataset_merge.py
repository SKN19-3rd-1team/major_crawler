"""
데이터셋 병합 스크립트

각 대학 폴더(hongik, hanyang, seoul, ewha)의 JSON 파일들을 하나로 병합합니다.
건국대(konkuk) 폴더는 이미 통합 파일이 있으므로 제외합니다.
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
        hongik_data["홍익대학교"]["공과대학"][dept_name] = courses
        print(f"[OK] 홍익대 - {dept_name}: {len(courses)}개 과목")

    return hongik_data


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

    # 1. 홍익대 데이터 병합
    print("\n[1] 홍익대학교 데이터 처리 중...")
    hongik_data = merge_hongik_data(data_dir)
    all_data = deep_merge_dicts(all_data, hongik_data)

    # 2. 한양대 데이터 병합
    print("\n[2] 한양대학교 데이터 처리 중...")
    hanyang_data = merge_standard_format_data(data_dir, "hanyang")
    all_data = deep_merge_dicts(all_data, hanyang_data)

    # 3. 서울대 데이터 병합
    print("\n[3] 서울대학교 데이터 처리 중...")
    seoul_data = merge_standard_format_data(data_dir, "seoul")
    all_data = deep_merge_dicts(all_data, seoul_data)

    # 4. 이화여대 데이터 병합
    print("\n[4] 이화여자대학교 데이터 처리 중...")
    ewha_data = merge_standard_format_data(data_dir, "ewha")
    all_data = deep_merge_dicts(all_data, ewha_data)

    # 5. 통합 데이터 저장
    print("\n" + "=" * 60)
    print("통합 데이터 저장 중...")

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(all_data, f, ensure_ascii=False, indent=2)

    print(f"[OK] 저장 완료: {output_path}")

    # 6. 통계 출력
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
