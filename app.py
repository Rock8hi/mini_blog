#!/root/blog/flask/venv/bin/python
# -*- coding: utf-8

from flask import Flask, url_for, make_response, abort, redirect, session, escape
from flask import request
from flask import render_template
from werkzeug.utils import secure_filename

import os
import re
import sys
import math
import codecs
import shutil
import hashlib
import logging
import markdown
from PIL import Image


# DEBUG_MODE = True
DEBUG_MODE = False


INPUT_PATH = 'markdown'
OUTPUT_PATH = 'static'
if not DEBUG_MODE:
    MAIN_DOMAIN_URL = 'http://www.kevengame.com/'
else:
    MAIN_DOMAIN_URL = 'http://127.0.0.1:5000/'


g_blog_list = {'tech': None, 'life': None}
g_markdown_mtime_dict = {'tech': {}, 'life': {}}
g_markdown_mtime_dict_for_blog = {}


app = Flask(__name__)
if not DEBUG_MODE:
    app.logger.setLevel(logging.INFO)
else:
    app.debug = True


def calc_file_md5(filename):
    if not os.path.exists(filename) or not os.path.isfile(filename):
        return
    if os.path.getsize(filename) > 64 * 1024:
        return
    with open(filename, 'rb') as f:
        md5obj = hashlib.md5()
        md5obj.update(f.read())
        return md5obj.hexdigest()


# @app.before_first_request  # 第1个请求到来执行
# def before_first_request1():
#     app.logger.debug('before_first_request1')
#
#
# @app.before_request  # 中间件 执行视图之前
# def before_request1():
#     app.logger.debug('before_request1')  # 不能有返回值，一旦有返回值在当前返回
#
#
# @app.before_request
# def before_request2():
#     app.logger.debug('before_request2')
#
#
# @app.after_request  # 中间件 执行视图之后
# def after_request1(response):
#     app.logger.debug('after_request1 ' + str(response))
#     return response
#
#
# @app.after_request  # 中间件 执行视图之后 先执行 after_request2
# def after_request2(response):
#     app.logger.debug('after_request2 ' + str(response))
#     return response


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


def format_date(year, month):
    if sys.version_info.major != 3:
        return '%s年%s月'.decode('utf-8') % (year, month)
    else:
        return '%s年%s月' % (year, month)


def convert_date(date):
    if sys.version_info.major != 3:
        return date.replace('年'.decode('utf-8'), '-').replace('月'.decode('utf-8'), '')
    else:
        return date.replace('年', '-').replace('月', '')


# 生成主页博客列表展示数据
def make_blog_list_data(**kwargs):
    type_filter = kwargs.get('type', 'tech')
    date_filter = kwargs.get('date', None)
    label_filter = kwargs.get('label', None)
    app.logger.debug('make_blog_list_data type_filter=%s; date_filter=%s; label_filter=%s'
                     % (type_filter, date_filter, label_filter))
    blog_list = []
    dates = set()
    labels = set()
    markdown_path = os.path.join(INPUT_PATH, type_filter)
    for f in os.listdir(markdown_path):
        ff = os.path.join(markdown_path, f)
        if not os.path.isfile(ff):
            continue
        # 刷新记录的文件修改时间
        g_markdown_mtime_dict[type_filter][ff] = os.path.getmtime(ff)
        # 提取markdown内的数据
        filename, suffix = os.path.splitext(f)
        if suffix != '.md' or filename == 'index':
            continue
        with codecs.open(ff, 'r', 'utf-8') as infile:
            comments = match_comment(infile.read())

            # 提取日期
            date = comments.get('date', '')
            split_date = []
            if len(date) != 0:
                split_date = date.split('/')
                if len(split_date) == 3:
                    dates.add(format_date(split_date[0], split_date[1]))

            # 提取标签
            split_label = comments.get('label', '').split(',')
            item_labels_with_url = {}
            if len(split_label) != 0:
                for label in split_label:
                    labels.add(label)
                    item_labels_with_url[label] = '%smarkdown/?label=%s' % (MAIN_DOMAIN_URL, label)

            if (date_filter is None and label_filter is None) \
                    or (date_filter is not None and date_filter == '%s-%s' % (split_date[0], split_date[1])) \
                    or (label_filter is not None and (label_filter in split_label)):
                # 博客列表内容
                blog_list.append({'title': comments.get('title', ''),
                                  'title_url': '%s%s/%s' % (MAIN_DOMAIN_URL, type_filter, f),
                                  'content': comments.get('desc', ''),
                                  'date': comments.get('date', ''),
                                  'labels': item_labels_with_url})

    dates_with_url = []
    dates = list(dates)
    dates.sort(reverse=True)
    for date in dates:
        dates_with_url.append((date, '%smarkdown/%s/?date=%s' % (MAIN_DOMAIN_URL, type_filter, convert_date(date))))

    labels_with_url = []
    labels = list(labels)
    labels.sort()
    for label in labels:
        labels_with_url.append((label, '%smarkdown/%s/?label=%s' % (MAIN_DOMAIN_URL, type_filter, label)))

    return {'abstracts': blog_list, 'dates': dates_with_url, 'labels': labels_with_url}


# 检查是否有变更的文件
def check_modified_markdown(**kwargs):
    type_filter = kwargs.get('type', 'tech')
    app.logger.debug('check_modified_markdown type_filter=%s' % type_filter)
    markdown_path = os.path.join(INPUT_PATH, type_filter)
    for f in os.listdir(markdown_path):
        ff = os.path.join(markdown_path, f)
        if not os.path.isfile(ff) or os.path.splitext(ff)[1] != '.md':
            continue
        # app.logger.debug('g_markdown_mtime_dict[%s]: %s' % (type_filter, g_markdown_mtime_dict[type_filter]))
        # app.logger.debug('file path: %s' % ff)
        # app.logger.debug('file path mtime: %s' % os.path.getmtime(ff))
        if g_markdown_mtime_dict[type_filter].get(ff) \
                and g_markdown_mtime_dict[type_filter][ff] == os.path.getmtime(ff):
            continue
        app.logger.debug('check result: bingo')
        return True
    return False


def check_markdown_list(type_filter):
    app.logger.debug('check_markdown_list type_filter=%s' % type_filter)
    global g_blog_list
    if g_blog_list[type_filter] is None or check_modified_markdown(type=type_filter):
        g_blog_list[type_filter] = make_blog_list_data(type=type_filter)


# 过滤出页面分类
def split_type_filter(file_path):
    split = file_path.split('/')
    return split[len(split) - 2]


# 转换markdown，并将html数据写入到文件
def make_markdown_html(file_path):
    app.logger.debug('make_markdown_html file path=%s' % file_path)
    type_filter = split_type_filter(file_path)
    check_markdown_list(type_filter)
    # 转换markdown为html，并存入文件
    markdown_path = os.path.join(INPUT_PATH, file_path)
    html_path = os.path.join(OUTPUT_PATH, os.path.splitext(file_path)[0] + '.html')
    with codecs.open(markdown_path, 'r', 'utf-8') as infile:
        check_dirs(html_path)
        with codecs.open(html_path, 'w', 'utf-8', errors='xmlcharrefreplace') as outfile:
            blog_html = markdown.markdown(infile.read(), extensions=['markdown.extensions.extra',
                                                                     'markdown.extensions.codehilite',
                                                                     'markdown.extensions.tables',
                                                                     'markdown.extensions.toc',
                                                                     'markdown.extensions.fenced_code',
                                                                     'markdown.extensions.smart_strong'])
            blog_html = blog_html.replace('<div class="codehilite">',
                                          '<div class="codehilite" style="overflow-x: auto;">')
            outfile.write(render_template('index.html',
                                          title='markdown',
                                          root_url=MAIN_DOMAIN_URL,
                                          labels=g_blog_list[type_filter]['labels'],
                                          dates=g_blog_list[type_filter]['dates'],
                                          blog_html=blog_html))
            app.logger.info('convert and write "%s" success' % file_path)


# 404 找不到资源
@app.errorhandler(404)
def page_not_found(error):
    app.logger.warning('page_not_found: %s' % error)
    return 'This page does not exist', 404


# 博客主页
@app.route('/index.html')
@app.route('/')
def show_index():
    app.logger.debug('show_index')
    check_markdown_list('tech')
    return render_template('index.html',
                           title='home',
                           root_url=MAIN_DOMAIN_URL,
                           labels=g_blog_list['tech']['labels'],
                           dates=g_blog_list['tech']['dates'],
                           blog_list=g_blog_list['tech']['abstracts'])


# 生活主页
@app.route('/life.html')
@app.route('/life')
def show_tab_life():
    app.logger.debug('show_tab_life')
    check_markdown_list('life')
    return render_template('life.html',
                           title='life',
                           root_url=MAIN_DOMAIN_URL,
                           labels=g_blog_list['life']['labels'],
                           dates=g_blog_list['life']['dates'],
                           blog_list=g_blog_list['life']['abstracts'])


@app.route('/tech.html')
def show_tab_tech():
    app.logger.debug('show_tab_tech')
    return render_template('tech.html', root_url=MAIN_DOMAIN_URL)


@app.route('/about.html')
def show_tab_about():
    app.logger.debug('show_tab_about')
    return render_template('about.html', root_url=MAIN_DOMAIN_URL)


@app.route('/markdown/tech/')
def show_tech_markdown_filter():
    date = request.args.get('date', None)
    label = request.args.get('label', None)
    app.logger.debug('show_tech_markdown_filter date=%s; label=%s' % (date, label))
    if date is None and label is None:
        return
    blog_list = make_blog_list_data(date=date, label=label)
    return render_template('index.html',
                           title='markdown filter',
                           root_url=MAIN_DOMAIN_URL,
                           labels=blog_list['labels'],
                           dates=blog_list['dates'],
                           blog_list=blog_list['abstracts'])


@app.route('/markdown/life/')
def show_life_markdown_filter():
    date = request.args.get('date', None)
    label = request.args.get('label', None)
    app.logger.debug('show_life_markdown_filter date=%s; label=%s' % (date, label))
    if date is None and label is None:
        return
    blog_list = make_blog_list_data(type='life', date=date, label=label)
    return render_template('life.html',
                           title='markdown filter',
                           root_url=MAIN_DOMAIN_URL,
                           labels=blog_list['labels'],
                           dates=blog_list['dates'],
                           blog_list=blog_list['abstracts'])


# 博客页面
def show_markdown(file_path):
    app.logger.debug('show_markdown file path=%s' % file_path)
    filename, suffix = os.path.splitext(file_path)
    if suffix != '.md':
        return show_static(file_path)
    f = os.path.join(INPUT_PATH, file_path)
    if os.path.exists(f) and os.path.isfile(f):
        # app.logger.debug('g_markdown_mtime_dict_for_blog: %s' % g_markdown_mtime_dict_for_blog)
        # app.logger.debug('file path: %s' % f)
        # app.logger.debug('file path mtime: %s' % os.path.getmtime(f))
        if not g_markdown_mtime_dict_for_blog.get(f) \
                or g_markdown_mtime_dict_for_blog[f] != os.path.getmtime(f) \
                or not os.path.exists(os.path.join(OUTPUT_PATH, '%s.html' % filename)):
            app.logger.debug('check result: bingo')
            make_markdown_html(file_path)
            g_markdown_mtime_dict_for_blog[f] = os.path.getmtime(f)
    else:
        abort(401)
    return app.send_static_file('%s.html' % filename)


@app.route('/tech/<file_path>')
def show_tech_markdown(file_path):
    app.logger.debug('show_tech_markdown file path=%s' % file_path)
    return show_markdown('tech/%s' % file_path)


@app.route('/life/<file_path>')
def show_life_markdown(file_path):
    app.logger.debug('show_life_markdown file path=%s' % file_path)
    return show_markdown('life/%s' % file_path)


# 上传文件
@app.route('/upload.html', methods=['GET'])
@app.route('/upload', methods=['POST'])
def show_upload_file():
    if request.method == 'GET':
        return app.send_static_file('upload.html')
    if request.method == 'POST':
        if not request.form.get('check_token'):
            return 'please input token.'
        if request.form['check_token'] != 'rock':
            return 'please use legal token.'
        if not request.files.get('upload_file'):
            return 'please select and upload file.'
        upload_file = request.files['upload_file']
        filename, suffix = os.path.splitext(secure_filename(upload_file.filename))
        if suffix != '.md' and suffix != '.png' and suffix != '.jpg' and suffix != '.gif':
            return "it's not support."
        upload_file.save(os.path.join(OUTPUT_PATH, secure_filename(upload_file.filename)))
        return 'congratulations, upload success.'


def check_dirs(file_path):
    if os.path.exists(file_path):
        return
    if os.path.splitext(file_path)[1] != '':
        file_path = file_path[: file_path.rfind(os.path.sep)]
        if os.path.exists(file_path):
            return
    os.makedirs(file_path)
    app.logger.info('make dirs(%s) success.' % file_path)


def check_static_image(file_path):
    app.logger.debug('copy_or_resize_image file path=%s' % file_path)
    filename, suffix = os.path.splitext(file_path)
    if suffix != '.png' and suffix != '.jpg' and suffix != '.gif':
        return
    input_image_path = os.path.join(INPUT_PATH, file_path)
    output_image_path = os.path.join(OUTPUT_PATH, file_path)
    if not os.path.exists(input_image_path) or not os.path.isfile(input_image_path):
        return
    type_filter = split_type_filter(file_path)
    if type_filter is None:
        return
    if g_markdown_mtime_dict[type_filter].get(input_image_path) \
            and g_markdown_mtime_dict[type_filter][input_image_path] == os.path.getmtime(input_image_path) \
            and os.path.exists(output_image_path):
        return
    img = Image.open(input_image_path, 'r')
    width, height = img.size
    if width > 480:
        ratio = 480 / width
        new_size = (480, int(math.floor(height * ratio)))
        check_dirs(os.path.join(OUTPUT_PATH, file_path))
        img.resize(new_size).save(os.path.join(OUTPUT_PATH, file_path))
        app.logger.debug('resize image success')
    else:
        if not os.path.exists(output_image_path)\
                or os.path.getmtime(input_image_path) != os.path.getmtime(output_image_path):
            check_dirs(output_image_path)
            shutil.copyfile(input_image_path, output_image_path)
            app.logger.debug('copy image success')
    g_markdown_mtime_dict[type_filter][input_image_path] = os.path.getmtime(input_image_path)


@app.route('/<path:file_path>')
def show_static(file_path):
    app.logger.debug('show_static file path=%s' % file_path)
    check_static_image(file_path)
    return app.send_static_file(file_path)


if __name__ == '__main__':
    app.run()
