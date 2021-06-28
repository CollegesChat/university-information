#!/usr/bin/env python3
# -*- encoding: utf-8 -*-

from slugify import slugify
import collections
import csv
import os
import re
import typing
import zhconv

questionnaire = [
    '宿舍是上床下桌吗？',
    '教室和宿舍有没有空调？',
    '有独立卫浴吗？没有独立浴室的话，澡堂离宿舍多远？',
    '有早自习、晚自习吗？',
    '有晨跑吗？',
    '每学期跑步打卡的要求是多少公里，可以骑车吗？',
    '寒暑假放多久，每年小学期有多长？',
    '学校允许点外卖吗，取外卖的地方离宿舍楼多远？',
    '学校交通便利吗，有地铁吗，在市区吗，不在的话进城要多久？',
    '宿舍楼有洗衣机吗？',
    '校园网怎么样？',
    '每天断电断网吗，几点开始断？',
    '食堂价格贵吗，会吃出异物吗？',
    '洗澡热水供应时间？',
    '校园内可以骑电瓶车吗，电池在哪能充电？',
    '宿舍限电情况？',
    '通宵自习有去处吗？',
    '大一能带电脑吗？',
    '学校里面用什么卡，饭堂怎样消费？',
    '学校会给学生发银行卡吗？',
    '学校的超市怎么样？',
    '学校的收发快递政策怎么样？',
    '学校里面的共享单车数目与种类如何？',
    '现阶段学校的门禁情况如何？',
    '宿舍晚上查寝吗，封寝吗，晚归能回去吗？']


NAME_PREPROCESS = re.compile(r'[\(\)（）【】#]')
FILENAME_PREPROCESS = re.compile(r'[/>|:&]')


class AnswerGroup:
    answers: list[str]

    def __init__(self):
        self.answers = []

    def add_answer(self, answer: str):
        self.answers.append(answer)

    def extend(self, other):
        self.answers.extend(other.answers)


class University:
    answers: list[AnswerGroup]
    additional_answers: list[str]
    credits: list[str]

    def __init__(self):
        self.answers = [AnswerGroup() for _ in range(len(questionnaire))]
        self.additional_answers = []
        self.credits = []

    def add_answer(self, index: int, answer: str):
        self.answers[index].add_answer(answer)

    def add_additional_answer(self, answer: str):
        self.additional_answers.append(answer)

    def add_credit(self, author: str):
        self.credits.append(author)

    def combine_from(self, other):
        for this, that in zip(self.answers, other.answers):
            this.extend(that)
        self.additional_answers.extend(other.additional_answers)
        self.credits.extend(other.credits)


class FilenameMap:
    mapping: dict[str, str]
    already_exists: set[str]

    def __init__(self):
        self.mapping = {}
        self.already_exists = set()

    def __getitem__(self, name: str):
        value = self.mapping.get(name)
        if value is None:
            value = slugify(FILENAME_PREPROCESS.sub('', name.replace(' ', '-')))
            index = 1
            while f'{value}-{index}' in self.already_exists:
                index += 1
            value = f'{value}-{index}'
            self.mapping[name] = value
            self.already_exists.add(value)
        return value


def markdown_escape(text: str):
    return text.replace('*', '\\*').replace('~', '\\~').replace('_', '\\_')


def join_path(*paths):
    # return os.path.join(*paths)
    return '/'.join(paths)


def main():
    # ===== read from csv =====
    with open('results_desensitized.csv', 'r', encoding='gb18030') as f:
        csv_reader = csv.reader(f)
        next(csv_reader)  # here we skip the first line

        universities = collections.defaultdict(University)
        filename_map = FilenameMap()

        for row in csv_reader:
            # unpack row into different parts, and ignore 8 items in the end.
            # `anonymous`: `2` means anonymous, and `1` not.
            # if `anonymous` is True, `email` is empty.
            _, _, anonymous, email, show_email, name, *answers = row[:-9]
            additional_answer = row[-9]

            # convert `anonymous` and `show_email` to boolean
            anonymous = True if int(anonymous) == 2 else False
            show_email = True if (not anonymous and float(show_email) == 1.0) else False

            # preprocess name
            name = zhconv.convert(name, 'zh-cn')
            name = NAME_PREPROCESS.sub('', name).strip()

            # if not exists, defaultdict will help create one
            university = universities[name]

            if not show_email or email == '':
                university.add_credit('匿名')
            else:
                university.add_credit(email)

            for index, answer in enumerate(answers):
                university.add_answer(index, answer)
            university.add_additional_answer(additional_answer)

    # ===== combine colleges =====
    with open('alias.txt', 'r', encoding='utf-8') as f:
        for line in f:
            name, *aliases = line.rstrip('\n').split('🚮')
            university = universities[name]
            for alias in aliases:
                university.combine_from(universities[alias])
                del universities[alias]
            if len(university.credits) == 0:
                del universities[name]
    del universities['trash_bin']

    # ===== write results =====
    os.makedirs('universities', exist_ok=True)
    for name, university in universities.items():
        filename = join_path('universities', filename_map[name]) + '.md'
        with open(filename, 'w', encoding='utf-8') as f:
            # write header
            f.write(f'# {name}\n\n')
            f.write('> 数据来源：{}\n\n'.format(' + '.join(university.credits)))

            # write answers
            assert len(questionnaire) == len(university.answers)
            for question, answers in zip(questionnaire, university.answers):
                f.write(f'## Q: {question}\n\n')
                for index, answer in enumerate(answers.answers, start=1):
                    f.write(f'- A{index}: {markdown_escape(answer)}\n\n')

            # write additional answers
            additional_answers = [ markdown_escape(text).replace('\n', '\n\n') for text in university.additional_answers if len(text) > 0 ]
            if len(additional_answers) > 0:
                f.write('## 自由补充部分\n\n')
                f.write('\n\n***\n\n'.join(additional_answers))

    with open('README.md', 'w', encoding='utf-8') as readme_f,\
         open('README_template.md', 'r', encoding='utf-8') as template_f:
        # first, copy template
        template = template_f.read()
        readme_f.write(template)
        readme_f.write('\n\n')

        # then, write university links
        university_names = list(universities.keys())
        university_names.sort()
        university_links = [ '[{}]({}.md)'.format(name, join_path('.', 'universities', filename_map[name])) for name in university_names ]
        readme_f.write('\n\n'.join(university_links))


if __name__ == '__main__':
    main()
