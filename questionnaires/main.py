# encoding = utf-8
import os
import csv

questionnaire = ["宿舍是上床下桌吗？", "教室和宿舍有没有空调？", "有独立卫浴吗？没有独立浴室的话，澡堂离宿舍多远？", "有早自习、晚自习吗？", "有晨跑吗？",
                 "每学期跑步打卡的要求是多少公里，可以骑车吗？", "寒暑假放多久，每年小学期有多长？", "学校允许点外卖吗，取外卖的地方离宿舍楼多远？", "学校交通便利吗，有地铁吗，在市区吗，不在的话进城要多久？",
                 "宿舍楼有洗衣机吗？", "校园网怎么样？", "每天断电断网吗，几点开始断？", "食堂价格贵吗，会吃出异物吗？", "洗澡热水供应时间？", "校园内可以骑电瓶车吗，电池在哪能充电？",
                 "宿舍限电情况？", "通宵自习有去处吗？", "大一能带电脑吗？", "学校里面用什么卡，饭堂怎样消费？", "学校会给学生发银行卡吗？", "学校的超市怎么样？", "学校的收发快递政策怎么样？",
                 "学校里面的共享单车数目与种类如何？", "现阶段学校的门禁情况如何？", "宿舍晚上查寝吗，封寝吗，晚归能回去吗？"]

with open('results.csv', 'r', encoding="gb18030") as csv_file:
    csv_reader = csv.reader(csv_file)
    output_buffers = []
    output_index_buffers = []
    # list to store the universities collected, {university: [index, count]}
    output_collected = {}
    next(csv_reader)  # here we skip the first line
    for row in csv_reader:
        try:
            output_index = output_collected[row[5]][0] - 1
            output_count = output_collected[row[5]][1]
            output_buffer_lines = output_buffers[output_index].splitlines()
            if int(row[2]) == 2 or float(row[4]) == 2.0 or str(row[3]) == '':
                output_buffer_lines[1] += " + 匿名数据"
            else:
                output_buffer_lines[1] += f" + 来自 {row[3]} 的数据"
        except KeyError:
            output_index = -1
            output_count = 0
            output_buffer_lines = [f"# {row[5]}"]
            if int(row[2]) == 2 or float(row[4]) == 2.0 or str(row[3]) == '':
                output_buffer_lines.append("> 匿名数据")
            else:
                output_buffer_lines.append(f"> 来自 {row[3]} 的数据")
        for index in range(6, len(row) - 9):
            if index - 6 < len(questionnaire):
                # add question when not exist
                if 2 + (output_count + 2) * (index - 6) >= len(output_buffer_lines)\
                        or not output_buffer_lines[2 + (output_count + 2) * (index - 6)].startswith("## Q"):
                    output_buffer_lines.insert(2 + (output_count + 2) * (index - 6), f"## Q: {questionnaire[index - 6]}")
            output_buffer_lines.insert(2 + (output_count + 2) * (index - 5) - 1, f"- A{output_count + 1}: {row[index]}")
        if row[len(row) - 9] != '':
            output_buffer_lines.append("***")
            output_buffer_lines.append(row[len(row) - 9])
        if output_index > 0:
            output_buffers[output_index] = "\n".join(output_buffer_lines)
            output_collected[row[5]][1] += 1
        else:
            output_buffers.append("\n".join(output_buffer_lines))
            output_collected[row[5]] = [len(output_buffers), 1]
    with open("README.md", 'w', encoding="utf-8") as output_readme_file:
        readme_template_file = open("README_template.md", 'r', encoding="utf-8")
        output_readme_file.write(readme_template_file.read())
        readme_template_file.close()
        try:
            os.mkdir("universities")
        except FileExistsError:
            pass
        for key in output_collected.keys():
            with open(f"universities/{key.replace(' ', '')}.md", 'w', encoding="utf-8") as output_item_file:
                output_item_file.write(output_buffers[output_collected[key][0] - 1].replace("\n", "\n\n"))
            output_index_buffers.append(f"\n\n[{key}](./universities/{key.replace(' ', '')}.md)")
        output_index_buffers.sort()
        output_readme_file.write("".join(output_index_buffers))
