"""
1. https://www.adiga.kr/ucp/uvt/uni/univView.do?menuId=PCUVTINF2000 링크의 html요소 분석
2. 각 대학의 univCd 추출 및 정리 (.json)
3. 모든 대학의 univCd 기반 접속 가능 여부 점검
- https://www.adiga.kr/ucp/uvt/uni/univDetail.do?menuId=PCUVTINF2000&unvCd={**univCd**}&searchSyr=2026
"""

import json
from bs4 import BeautifulSoup
from pathlib import Path

def extract_university_codes(html_file_path, output_json_path):
    """
    HTML 파일에서 대학 코드와 이름을 추출하여 JSON 파일로 저장
    
    Args:
        html_file_path: 입력 HTML 파일 경로
        output_json_path: 출력 JSON 파일 경로
    """
    # HTML 파일 읽기
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # BeautifulSoup으로 파싱
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # univGroupInput 클래스를 가진 모든 input 요소 찾기
    university_inputs = soup.find_all('input', class_='univGroupInput')
    
    # 대학 정보를 저장할 딕셔너리
    universities = {}
    
    # 각 input 요소에서 value와 label 추출
    for input_tag in university_inputs:
        # value 속성에서 대학 코드 추출
        univ_code = input_tag.get('value')
        
        # id 속성에서 label의 for 속성과 매칭
        input_id = input_tag.get('id')
        
        # 해당 input의 label 찾기
        label = soup.find('label', {'for': input_id})
        
        if label and univ_code:
            # label 텍스트에서 대학명 추출 (strong 태그 제외)
            univ_name = label.get_text(strip=True)
            # strong 태그의 텍스트 제거 (예: "1건")
            strong_tag = label.find('strong')
            if strong_tag:
                univ_name = univ_name.replace(strong_tag.get_text(strip=True), '').strip()
            
            # 딕셔너리에 추가
            universities[univ_name] = univ_code
    
    # JSON 파일로 저장
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(universities, f, ensure_ascii=False, indent=2)
    
    print(f"총 {len(universities)}개의 대학 정보를 추출했습니다.")
    print(f"결과가 {output_json_path}에 저장되었습니다.")
    
    # 처음 5개 샘플 출력
    print("\n샘플 데이터:")
    for i, (name, code) in enumerate(list(universities.items())[:5]):
        print(f"  {name}: {code}")
    
    return universities


def check_university_accessibility(universities_dict, output_json_path, search_year=2026):
    """
    각 대학의 univCd로 접속 가능 여부를 점검
    
    Args:
        universities_dict: 대학명과 코드가 담긴 딕셔너리
        output_json_path: 결과를 저장할 JSON 파일 경로
        search_year: 검색 학년도 (기본값: 2026)
    """
    import requests
    from time import sleep
    
    base_url = "https://www.adiga.kr/ucp/uvt/uni/univDetail.do"
    results = {}
    
    total = len(universities_dict)
    print(f"\n총 {total}개 대학의 접속 가능 여부를 점검합니다...")
    print("=" * 60)
    
    for idx, (univ_name, univ_code) in enumerate(universities_dict.items(), 1):
        # URL 생성
        url = f"{base_url}?menuId=PCUVTINF2000&unvCd={univ_code}&searchSyr={search_year}"
        
        try:
            # HTTP 요청
            response = requests.get(url, timeout=10)
            status_code = response.status_code
            accessible = status_code == 200
            
            # 결과 저장
            results[univ_name] = {
                "code": univ_code,
                "url": url,
                "status_code": status_code,
                "accessible": accessible,
                "response_time_ms": int(response.elapsed.total_seconds() * 1000)
            }
            
            # 진행 상황 출력
            status_icon = "✓" if accessible else "✗"
            print(f"[{idx}/{total}] {status_icon} {univ_name} (코드: {univ_code}) - {status_code}")
            
        except requests.exceptions.Timeout:
            results[univ_name] = {
                "code": univ_code,
                "url": url,
                "status_code": None,
                "accessible": False,
                "error": "Timeout"
            }
            print(f"[{idx}/{total}] ✗ {univ_name} (코드: {univ_code}) - Timeout")
            
        except requests.exceptions.RequestException as e:
            results[univ_name] = {
                "code": univ_code,
                "url": url,
                "status_code": None,
                "accessible": False,
                "error": str(e)
            }
            print(f"[{idx}/{total}] ✗ {univ_name} (코드: {univ_code}) - Error: {str(e)[:50]}")
        
        # 서버 부하 방지를 위한 딜레이
        sleep(0.5)
    
    # 결과를 JSON 파일로 저장
    with open(output_json_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # 통계 출력
    print("\n" + "=" * 60)
    accessible_count = sum(1 for r in results.values() if r.get('accessible', False))
    print(f"\n✅ 접속 가능: {accessible_count}개")
    print(f"❌ 접속 불가: {total - accessible_count}개")
    print(f"\n결과가 {output_json_path}에 저장되었습니다.")
    
    return results


if __name__ == "__main__":
    # 파일 경로 설정
    script_dir = Path(__file__).parent
    html_file = script_dir / "outer_html.html"
    output_file = script_dir / "university_codes.json"
    accessibility_file = script_dir / "university_accessibility.json"
    
    # 1단계: 대학 코드 추출
    print("=" * 60)
    print("1단계: HTML에서 대학 코드 추출")
    print("=" * 60)
    universities = extract_university_codes(html_file, output_file)
    
    # 2단계: 접속 가능 여부 점검
    print("\n" + "=" * 60)
    print("2단계: 각 대학 URL 접속 가능 여부 점검")
    print("=" * 60)
    accessibility_results = check_university_accessibility(universities, accessibility_file)