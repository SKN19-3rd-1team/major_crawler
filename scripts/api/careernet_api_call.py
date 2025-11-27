import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

career_net_api_key = os.getenv('CAREER_NET_API_KEY')
career_net_api_url = os.getenv('CAREER_NET_API_URL')

def fetch_major_detail():
    params = {
        "apiKey": career_net_api_key,
        "svcType": "api",
        "svcCode": "MAJOR_VIEW",
        "contentType": "json",
        "gubun": "univ_list",
        "univSe": "univ",
        "majorSeq": 30
    }

    response = requests.get(career_net_api_url, params=params)
    response.raise_for_status()

    data = response.json()
    return data


def save_json(data, filename="data/raw/major_detail.json"):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
    print(f"JSON 저장 완료: {filename}")


if __name__ == "__main__":
    major_data = fetch_major_detail()
    save_json(major_data)