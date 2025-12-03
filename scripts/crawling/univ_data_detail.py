import requests
from urllib.parse import quote
import json
import os
from dotenv import load_dotenv

load_dotenv()
SERVICE_API_KEY = os.getenv("SERVICE_API_KEY")

if not SERVICE_API_KEY:
    raise RuntimeError(
        "SERVICE_API_KEY가 설정되어 있지 않습니다. "
        ".env 파일에 SERVICE_API_KEY=인증키 형태로 추가했는지 확인하세요."
    )

univ_api_url = "http://api.data.go.kr/openapi/tn_pubr_public_univ_major_api"

# 인코딩
encoded_service_key = quote(SERVICE_API_KEY, safe='')   # 서비스키 URLEncoder
yr = quote("2024")                                      # 연도
lssn_term = quote("4년")                                # 수업연한
deg_crse = quote("학사")                                # 학위과정
scsbjt_status = quote("기존")                           # 학과상태
schl_se = quote("대학교")                               # 학교구분

total_data = []

def fetch_all_pages():
    page = 1

    while True:
        # HTTP URL 사용
        URL = (
            f"{univ_api_url}"
            f"?serviceKey={encoded_service_key}"
            f"&pageNo={page}"
            f"&numOfRows=500"
            f"&type=json"
            f"&YR={yr}"
            f"&LSSN_TERM={lssn_term}"
            f"&DEG_CRSE_CRS_NM={deg_crse}"
            f"&SCSBJT_STTS_NM={scsbjt_status}"
            f"&SCHL_SE_NM={schl_se}"
        )

        # API 호출
        response = requests.get(URL, timeout=15)
        try:
            data = response.json()
        except ValueError:
            print("[ERROR] JSON 파싱 실패")
            print(response.text)
            exit()

        # items 가져오기
        body = data.get("response", {}).get("body", {})
        items_wrapper = body.get("items", {})
        items = items_wrapper.get("item", []) if isinstance(items_wrapper, dict) else items_wrapper

        print(f"[INFO] 총 아이템 수: {len(items)}")

        # 더이상 데이터가 없으면 종료
        if not items:
            print(f"[INFO] 페이지 {page}에서 item 0개")
            break

        total_data.extend(items)
        page += 1

    return total_data

# JSON 저장
def save_json(filename="data/raw/univ_data_detail.json"):
    univ_data = fetch_all_pages()
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(univ_data, f, ensure_ascii=False, indent=2)

    print(f"JSON 저장 완료: {filename}")

if __name__ == "__main__":
    save_json()