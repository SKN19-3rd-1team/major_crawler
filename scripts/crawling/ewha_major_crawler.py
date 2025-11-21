# https://www.ewha.ac.kr/ewha/bachelor/curriculum-major.do
# https://eureka.ewha.ac.kr/eureka/my/public.do?pgId=P532004170

import json
import pdfplumber
import pandas as pd

university_name = "이화여자대학교"
colleges = ["공과대학", "자연과학대학", "인공지능대학"]
JSON_FILE = f"data/raw/ewha_syllabus.json"
data = {university_name: {}}

def extract_data_from_pdf(file_path):
    with pdfplumber.open(file_path) as f:
        pages = f.pages
        tables = []
        for page in pages:
            table = page.extract_table()
            tables.extend(table)

        df = pd.DataFrame(tables[7:], columns=[tables[6]])
        print(df)
        return df
                                     
def data_parse(file_path, college):
    df = extract_data_from_pdf(file_path)

    for _, row in df.iterrows():
        dept_name = str(row['설정전공']).strip().replace('\n', '')
        course_name = str(row['교과목명']).strip().replace('\n', '')
        description = str(row['교과목기술(국문)']).strip().replace('\n', ' ')

        if (dept_name not in "None"  or course_name not in "None" or description not in "None"):
            if dept_name != "설정전공":
                # JSON 구조
                if college not in data[university_name]:
                    data[university_name][college] = {}
                if dept_name not in data[university_name][college]:
                    data[university_name][college][dept_name] = []
                data[university_name][college][dept_name].append({
                    "name": course_name,
                    "description": description.replace('\n', ' ').strip() 
                })

def run():
    for college in colleges:
        file_path = f'data/raw/2025_ewha_{college}_전공과목개요.pdf'
        data_parse(file_path, college)

    # JSON 저장
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        print('저장: ', JSON_FILE)

if __name__ == "__main__":
    run()