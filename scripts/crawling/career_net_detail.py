import requests
import os
import json
from dotenv import load_dotenv

load_dotenv()

career_net_api_key = os.getenv('CAREER_NET_API_KEY')
career_net_api_url = os.getenv('CAREER_NET_API_URL')

total_data = []

def fetch_major_detail():
    with open('data/raw/major_list.json', 'r', encoding='utf-8') as f:
        data = json.load(f)

    majorSeq_list = []

    for item in data:
        content_list = item["dataSearch"]["content"]

        for content in content_list:
            lClass = content["lClass"]  # 공학계열 / 자연계열

            if lClass == "공학계열":
                subject = 100394
            elif lClass == "자연계열":
                subject = 100395
            else:
                subject = None

            majorSeq_list.append({
                "majorSeq": content["majorSeq"],
                "subject": subject
            })

    for item  in majorSeq_list:
        subject = item["subject"]
        seq = item["majorSeq"]
        
        params = {
            "apiKey": career_net_api_key,
            "svcType": "api",
            "svcCode": "MAJOR_VIEW",
            "contentType": "json",
            "gubun": "univ_list",
            "univSe": "univ",
            "subject": subject,
            "majorSeq": seq,
        }

        response = requests.get(career_net_api_url, params=params)
        response.raise_for_status()

        data = response.json()
        total_data.append(data)

    return total_data


def save_json(filename="data/raw/major_detail.json"):
        major_data = fetch_major_detail()
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(major_data, f, ensure_ascii=False, indent=4)
        print(f"JSON 저장 완료: {filename}")


if __name__ == "__main__":
    save_json()