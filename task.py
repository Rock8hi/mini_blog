#!/root/blog/flask/venv/bin/python
# -*- coding:utf-8 -*-

import os
import re
import codecs
import random
import hashlib
from dbhelper import thumbnail_helper


INPUT_PATH = 'markdown'
OUTPUT_PATH = 'static'


def calc_file_md5(filename):
    if not os.path.exists(filename) or not os.path.isfile(filename):
        return
    if os.path.getsize(filename) > 64 * 1024:
        return
    with open(filename, 'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        return md5obj.hexdigest()


# 过滤出markdown中的日期、标签、描述等信息
def match_comment(markdown_string=''):
    pattern1 = re.compile(r"<!--([\s\S]*?)-->")
    pattern2 = re.compile(r"(?<=<!--)[\s\S]*(?=-->)")
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
        date = comments.get('date', '')
        label = comments.get('label', '')
        desc = comments.get('desc', '')
        md5 = calc_file_md5(md_path)
        mtime = os.path.getmtime(md_path)

        md_path = md_path.replace(os.sep, '/')
        category = md_path.split('/')[1]
        html_path = os.path.splitext(md_path.replace(INPUT_PATH, OUTPUT_PATH, 1))[0] + '.html'
        read_count = random.randint(128, 512)

        if insert:
            data = [(category, title, date, label, desc, md_path, str(md5), str(mtime), html_path, read_count)]
            thumbnail_helper.save(data)
        else:
            data = [(title, date, label, desc, str(md5), str(mtime), md_path)]
            thumbnail_helper.update_thumbnail(data)


def check_markdown(md_path):
    md_path = md_path.replace(os.sep, '/')
    result = thumbnail_helper.fetchone(md_path)
    if result is None:
        return
    if len(result) == 0:
        update_markdown_thumbnail(md_path)
        return
    if float(result[0][8]) != os.path.getmtime(md_path):
        update_markdown_thumbnail(md_path, False)
        return
    print('not update: ', md_path)


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
    thumbnail_helper.init()
    walk_markdown(INPUT_PATH)
    for item in thumbnail_helper.fetchall():
        print(item)


if __name__ == '__main__':
    run()
