"""
대학 접속 정보 데이터 전처리 스크립트

university_accessibility.json 파일에서 불필요한 항목을 제거하고
code와 url만 남긴 정제된 데이터를 생성합니다.

제거 항목:
- status_code
- accessible
- response_time_ms

유지 항목:
- code (대학 코드)
- url (대학 상세 페이지 URL)
"""

import json
from pathlib import Path


def preprocess_university_data(input_path, output_path):
    """
    대학 접속 정보에서 불필요한 항목 제거
    
    Args:
        input_path: 원본 JSON 파일 경로
        output_path: 전처리된 JSON 파일 저장 경로
    """
    # 원본 데이터 로드
    with open(input_path, 'r', encoding='utf-8') as f:
        original_data = json.load(f)
    
    # 전처리: status_code, accessible, response_time_ms 제거
    preprocessed_data = {}
    removed_fields = ['status_code', 'accessible', 'response_time_ms']
    
    for univ_name, univ_info in original_data.items():
        # 새로운 딕셔너리 생성 (code, url만 포함)
        preprocessed_data[univ_name] = {
            'code': univ_info['code'],
            'url': univ_info['url']
        }
    
    # 전처리된 데이터 저장
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(preprocessed_data, f, ensure_ascii=False, indent=2)
    
    # 통계 출력
    print("=" * 60)
    print("대학 데이터 전처리 완료")
    print("=" * 60)
    print(f"입력 파일: {input_path}")
    print(f"출력 파일: {output_path}")
    print(f"\n총 대학 수: {len(preprocessed_data)}개")
    print(f"제거된 필드: {', '.join(removed_fields)}")
    print(f"유지된 필드: code, url")
    
    # 샘플 데이터 출력
    print("\n샘플 데이터 (처음 3개):")
    print("-" * 60)
    for i, (name, info) in enumerate(list(preprocessed_data.items())[:3]):
        print(f"\n{i+1}. {name}")
        print(f"   - 코드: {info['code']}")
        print(f"   - URL: {info['url']}")
    
    return preprocessed_data


if __name__ == "__main__":
    # 프로젝트 루트 디렉토리 기준 경로 설정
    project_root = Path(__file__).parent.parent
    
    # 입력 파일 경로
    input_file = project_root / "data" / "raw" / "university_accessibility.json"
    
    # 출력 파일 경로
    output_file = project_root / "data" / "preprocessed" / "university_data_cleaned.json"
    
    # 전처리 실행
    preprocessed_data = preprocess_university_data(input_file, output_file)
    
    print("\n" + "=" * 60)
    print("✅ 전처리가 성공적으로 완료되었습니다!")
    print("=" * 60)
