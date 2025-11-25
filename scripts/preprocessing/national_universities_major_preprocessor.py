import json
import pandas as pd
import glob, os

'''
기존 JSON 구조
강원대학교.json
{
  "간호대학": {
    "간호학과": {
      "철학의이해": [
        {
          "연도": 2022,
          "학년": "1",
          "학기": 1,
          "학점": 3.0,
          "이론시간": 3.0,
          "실습시간": 0,
          "과목구분": "교양",
          "학습목표": "가. 철학의 주요 개념을 이해함으로써 철학이 어떠한 학문인지를 설명할 수 있다.나. 철학의 주요 쟁점과 논쟁들을 이해하고, 이에 대한 비판적 수용을 통해서 자신과 자신을 둘러싼 세계를 새로운 관점에서 볼 수 있다.",
          "주교재": "1. 주교재는 따로 없고 강의자가 수업자료를 제공할 예정.2. 참고문헌ª철학의 개념과 주요문제ª, 백종현, 철학과 현실사, 2007.ª논리 그리고 비판적 사고ª, 비판적사고교재연구회, 글고운, 2019.ª세계 철학사ª, 한스 요하힘 슈퇴리히, 박민수 역, 자음과모음, 2008.ª서양미술사ª, 에른스트 곰브리치, 백승길,이종숭 역, 예경, 2003.ª윤리학: 옳고 그름의 발견ª(개정판), 제임스 피저, 류지한 회 역, 울력, 2019.ª실존주의자로 사는 법ª, 게리 콕스, 지여울 역, 황소걸음, 2012.ª정의란 무엇인가ª, 마이클 샌델, 이창신 역, 김영사, 2010.",
          "부교재": "",
          "참고자료": "",
          "선행학습자료": "없음"
        },
'''

'''
전처리 후 구조
{
  "강원대학교": {
    "간호대학": {
      "간호학과": [
        {
          "grade_semester": "1-1",
          "name":"철학의이해",
          "course_classification": "교양",
          "description": "가. 철학의 주요 개념을 이해함으로써 철학이 어떠한 학문인지를 설명할 수 있다.나. 철학의 주요 쟁점과 논쟁들을 이해하고, 이에 대한 비판적 수용을 통해서 자신과 자신을 둘러싼 세계를 새로운 관점에서 볼 수 있다."
        },
'''

file_path = 'data/raw/national_universities/*.json'
all_files = glob.glob(file_path)

# 파일 저장명 맵핑
NAME = {
    "강원대학교":"gangwon",
    "경북대학교":"gyunbook",
    "경상국립대학교":"gyungsang",
    "부산대학교":"busan",
    "전북대학교":"junbook",
    "제주대학교":"jeju",
    "충남대학교":"gangwon",
    "충북대학교":"chungbook",
}

data = {}

# 전처리 함수                            
def preprocess_data():
  for file in all_files:
    # 파일 로드
    university_name = os.path.basename(file).split('.')[0]
  
    with open(file, 'r', encoding='utf-8') as f:
        content = json.load(f)
        
    if university_name not in data:
        data[university_name] = {}

    for college, college_data in content.items():
        if college not in data[university_name]:
            data[university_name][college] = {}

        for dept_name, dept_data in college_data.items():
            if dept_name not in data[university_name][college]:
                data[university_name][college][dept_name] = []

                for subject_name, syllabus_list in dept_data.items():
                    if syllabus_list:
                      syllabus_detail = syllabus_list[0]

                      grade = str(syllabus_detail.get("학년", ""))
                      semester = str(syllabus_detail.get("학기", ""))
                      course_classification = str(syllabus_detail.get("과목구분", ""))
                      description = str(syllabus_detail.get("학습목표", ""))
                  
                      data[university_name][college][dept_name].append({
                          "grade_semester": f'{grade}-{semester}',
                          "course_classification": course_classification,
                          "name": subject_name,
                          "description": description
                      })
  return data

# 학교마다 JSON 저장
def run():
    processed_data = preprocess_data()
    print(processed_data)

    for university_ko_name, university_data in processed_data.items():
        university_en_name = NAME.get(university_ko_name, 'unknown')
        JSON_FILE = f"./data/preprocessed/{university_en_name}_syllabus.json"

        final_data_to_save = {
          university_ko_name: university_data
        }

        with open(JSON_FILE, "w", encoding="utf-8") as f:
            json.dump(final_data_to_save, f, ensure_ascii=False, indent=4)
            print('저장: ', JSON_FILE)

if __name__ == "__main__":
    run()
