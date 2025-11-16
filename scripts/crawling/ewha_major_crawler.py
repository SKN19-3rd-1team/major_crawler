# https://www.ewha.ac.kr/ewha/bachelor/curriculum-major.do
# https://eureka.ewha.ac.kr/eureka/my/public.do?pgId=P532004170

import json
from langchain_community.document_loaders import PyPDFLoader

university_name = "이화여자대학교"
colleges = ["공과대학", "자연과학대학"]
JSON_FILE = f"data/raw/ewha_syllabus.json"
data = {university_name: {}}

def file_parse(file_path, college):
    loader = PyPDFLoader(file_path)
    documents = loader.load()

    raw_text = " ".join([doc.page_content for doc in documents])
    lines = raw_text.strip().split('\n')

    header = lines[0].split()

    for line in lines:
        line = line.strip()
        if not line:
            continue
        print(line)
        
        dept_name = line[1].strip()
        course_name = line[3].strip()
        description = line[5].strip()

        # 5. JSON 형식
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
        file_parse(file_path, college)

    # JSON 저장
    with open(JSON_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)
        print('저장: ', JSON_FILE)

if __name__ == "__main__":
    run()