import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

career_net_api_key = os.getenv('CAREER_NET_API_KEY')
career_net_api_url = os.getenv('CAREER_NET_API_URL')

total_data = []

def fetch_major_list():
    subject = [
        100394, # 공학계열
        100395  # 자연계열
    ]

    for i in range(len(subject)):
        params = {
            "apiKey": career_net_api_key,
            "svcType": "api",
            "svcCode": "MAJOR",
            "contentType": "json",
            "gubun": "univ_list",
            "univSe": "univ",
            "subject": subject[i],
            "thisPage": 1,
            "perPage": 1000
        }

        response = requests.get(career_net_api_url, params=params)
        response.raise_for_status()

        data = response.json()
        total_data.append(data)
    return total_data


def save_json(filename="data/raw/major_list.json"):
        major_data = fetch_major_list()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(major_data, f, ensure_ascii=False, indent=4)
        print(f"JSON 저장 완료: {filename}")


if __name__ == "__main__":
    save_json()