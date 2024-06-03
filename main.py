import os
import re
import csv

def parse_markdown(md_content):
    # 定义正则表达式模式
    q_pattern = re.compile(r'^## Q: (.+)$', re.MULTILINE)
    a_pattern = re.compile(r'^- (\w+): (.+)$', re.MULTILINE)
    
    # 初始化数据存储结构
    questions = []
    answers = {}
    
    # 分割内容并逐行处理
    lines = md_content.split('\n')
    current_question = ''
    
    for line in lines:
        q_match = q_pattern.match(line)
        a_match = a_pattern.match(line)
        
        if q_match:
            current_question = q_match.group(1)
            questions.append(current_question)
            answers[current_question] = []
        elif a_match:
            respondent, answer = a_match.groups()
            if current_question:
                answers[current_question].append(answer)
    
    return questions, answers

def save_combined_csv(combined_data, output_file):
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        
        # 写入表头
        header = ['University'] + combined_data['questions']
        writer.writerow(header)
        
        # 写入每个大学的每个问题的答案
        for university, data in combined_data['universities'].items():
            row = [university]
            for question in combined_data['questions']:
                if question in data:
                    row.append('\n\n'.join(data[question]))
                else:
                    row.append('无')
            writer.writerow(row)
            print(f"Wrote row: {row}")

def process_files_in_directory(path):
    combined_data = {'universities': {}, 'questions': []}
    
    for root, dirs, files in os.walk(path):
        for file in files:
            if file.endswith('.md'):
                file_path = os.path.join(root, file)
                print(f"Processing file: {file_path}")
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        md_content = f.read()
                    
                    # 提取大学名称（第一行内容去掉'# '）
                    university_name_match = re.match(r'^# (.+)', md_content.split('\n')[0])
                    university_name = university_name_match.group(1) if university_name_match else os.path.splitext(file)[0]
                    
                    questions, answers = parse_markdown(md_content)
                    if questions and answers:
                        combined_data['questions'].extend(q for q in questions if q not in combined_data['questions'])
                        combined_data['universities'][university_name] = answers
                    else:
                        print(f"No questions or answers found in file: {file_path}")
                except Exception as e:
                    print(f"Failed to process file {file_path}: {e}")
    
    # 保存为一个大表格
    output_file = os.path.join(os.path.dirname(path), 'combined_universities.csv')
    save_combined_csv(combined_data, output_file)
    print(f"Combined CSV file saved: {output_file}")

# 指定要遍历的目录路径
path = r'./docs/universities'

# 处理该目录下的所有文件
process_files_in_directory(path)
