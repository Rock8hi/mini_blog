#!/root/blog/flask/venv/bin/python
# -*- coding:utf-8 -*-

import os
import re
import codecs
import random
from dbhelper import thumbnail_helper as helper
import utils


MARKDOWN_PATH = 'markdown'


# 过滤出markdown中的日期、标签、描述等信息
def match_comment(markdown_string=''):
    pattern1 = re.compile(r'<!--([\s\S]*?)-->')
    pattern2 = re.compile(r'(?<=<!--)[\s\S]*(?=-->)')
    result = {}
    if len(markdown_string) == 0:
        return
    for matcher1 in pattern1.finditer(markdown_string):
        s1 = matcher1.group().strip()
        for matcher2 in pattern2.finditer(s1):
            s2 = matcher2.group().strip()
            split_pos = s2.find(':')
            if split_pos == -1:
                continue
            left_brace_pos = s2.find('{', split_pos + 1)
            if left_brace_pos == -1:
                continue
            right_brace_pos = s2.rfind('}')
            if right_brace_pos == -1:
                continue
            key = s2[:split_pos].strip()
            value = s2[left_brace_pos + 1:right_brace_pos].strip()
            result[key] = value
    return result


def update_markdown_thumbnail(md_path, insert=True):
    with codecs.open(md_path, 'r', 'utf-8') as infile:
        comments = match_comment(infile.read())

        title = comments.get('title', '')
        date = comments.get('date', '').replace('/', '-')
        dates = date.split('-')
        if len(dates) == 3:
            date = dates[0]
            date += '-'
            date += dates[1] if len(dates[1]) != 1 else '0' + dates[1]
            date += '-'
            date += dates[2] if len(dates[2]) != 1 else '0' + dates[2]
        label = comments.get('label', '')
        desc = comments.get('desc', '')
        md_path = utils.fix_sep(md_path, '/')

        if insert:
            mtime = os.path.getmtime(md_path)
            category = md_path.split('/')[1]
            hits = random.randint(128, 512)
            data = [(category, title, date, label, desc, md_path, mtime, hits)]
            helper.save(data)
        else:
            # 更新db内数据时，只更新markdown内容数据，不更新mtime。
            # 当请求某个markdown网页时，db内的mtime与markdown文件的mtime做对比，
            # 如果对比不一致，则重新生成markdown网页并保存，然后更新db内的mtime
            data = [(title, date, label, desc, md_path)]
            helper.update_thumbnail(data)


def check_markdown(md_path):
    md_path = utils.fix_sep(md_path, '/')
    result = helper.fetchone(md_path)
    if result is None:
        return
    if len(result) == 0:
        update_markdown_thumbnail(md_path)
        return
    if result[0][helper.MODIFIED_TIME] != os.path.getmtime(md_path):
        update_markdown_thumbnail(md_path, False)
        return
    # print('not update: ', md_path)


def walk_markdown(dir_path):
    for f in os.listdir(dir_path):
        ff = os.path.join(dir_path, f)
        if os.path.isdir(ff):
            walk_markdown(ff)
        if not os.path.isfile(ff):
            continue
        suffix = os.path.splitext(ff)[1]
        if suffix != '.md':
            continue
        check_markdown(ff)


def run():
    helper.init()
    walk_markdown(MARKDOWN_PATH)
    # for item in helper.fetchall():
    #     print(item)


if __name__ == '__main__':
    run()
