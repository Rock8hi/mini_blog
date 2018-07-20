#!/root/blog/flask/venv/bin/python
# -*- coding:utf-8 -*-

from flask import Flask, url_for, redirect
from flask import request
from flask import render_template
from werkzeug.utils import secure_filename

import os
import re
import codecs
import shutil
import markdown
from dbhelper import thumbnail_helper as thumbnail
from dbhelper import hits_helper as hits


app = Flask(__name__)
# app.debug = True
app.debug = False

thumbnail.init(app.debug)
hits.init(app.debug)


INPUT_PATH = os.path.join(app.root_path, 'markdown')
OUTPUT_PATH = app.static_folder


@app.before_first_request
def before_first_request():
    app.logger.debug('before_first_request')


@app.before_request
def before_request():
    app.logger.debug('before_request')
    update_hits()


def update_hits():
    hits.save(get_ip(), request.path)


def get_ip():
    if 'X-Forwarded-For' not in request.headers:
        return '0.0.0.0'
    ip = request.headers['X-Forwarded-For']
    ips = ip.split(',')
    if len(ips) > 1:
        return ips[1]
    return ip


# 过滤出页面分类
def split_category(file_path):
    file_path = file_path.replace(os.sep, '/')
    split = file_path.split('/')
    return split[len(split) - 2]


def gen_tabs(category):
    return [('主页', url_for('show_index'), category == 'tech'),
            ('技术', url_for('show_tab_tech')),
            ('生活', url_for('show_tab_life'), category == 'life'),
            ('关于', url_for('show_tab_about'))]


# 转换markdown，并将html数据写入到文件
def make_markdown_html(file_path):
    app.logger.debug('make_markdown_html file_path = %s' % file_path)
    category = split_category(file_path)
    blog_list = calc_markdown_thumbnail_list(category=category)
    # 转换markdown为html，并存入文件
    markdown_path = os.path.join(INPUT_PATH, file_path).replace(os.sep, '/')
    html_path = os.path.join(OUTPUT_PATH, os.path.splitext(file_path)[0] + '.html').replace(os.sep, '/')
    with codecs.open(markdown_path, 'r', 'utf-8') as infile:
        check_dirs(html_path)
        with codecs.open(html_path, 'w', 'utf-8', errors='xmlcharrefreplace') as outfile:
            blog_html = markdown.markdown(infile.read(), extensions=['markdown.extensions.extra',
                                                                     'markdown.extensions.codehilite',
                                                                     'markdown.extensions.tables',
                                                                     'markdown.extensions.toc',
                                                                     'markdown.extensions.fenced_code',
                                                                     'markdown.extensions.smart_strong'])
            blog_html = blog_html.replace(r'<div class="codehilite">',
                                          r'<div class="codehilite" style="overflow-x: auto;">')
            blog_html = re.sub(r'<img\s*(.*?)\s*/>',
                               r'<img \1 style="border: 2px solid #56d0f9; max-width: 480px; vertical-ali'
                               r'gn: text-bottom;" />',
                               blog_html)
            outfile.write(render_template('index.html',
                                          title='markdown',
                                          tabs=gen_tabs(category),
                                          labels=blog_list['labels'],
                                          dates=blog_list['dates'],
                                          blog_html=blog_html))
            app.logger.info('convert and write "%s" success' % file_path)


# 404 找不到资源
@app.errorhandler(404)
def page_not_found(error):
    app.logger.warning('page_not_found: %s' % error)
    return 'This page does not exist', 404


def calc_markdown_thumbnail_list(**kwargs):
    category_filter = kwargs.get('category', 'tech')
    date_filter = kwargs.get('date', None)
    label_filter = kwargs.get('label', None)
    app.logger.debug('calc_markdown_thumbnail_list category_filter=%s; date_filter=%s; label_filter=%s'
                     % (category_filter, date_filter, label_filter))

    data = thumbnail.fetchgroup(category_filter)
    if data is None or len(data) == 0:
        return {'outlines': [], 'dates': [], 'labels': []}

    blog_list = []
    dates = set()
    labels = set()

    for item in data:
        # 提取日期
        date = item[thumbnail.DATE]
        split_date = []
        if len(date) != 0:
            split_date = date.replace('/', '-').split('-')
            if len(split_date) == 3:
                dates.add(split_date[0] + '-' + split_date[1])

        # 提取标签
        split_label = item[thumbnail.LABEL].split(',')
        item_labels_with_url = {}
        if len(split_label) != 0:
            for label in split_label:
                labels.add(label)
                item_labels_with_url[label] = url_for('show_%s_filter' % category_filter, label=label)

        if (date_filter is None and label_filter is None) \
                or (date_filter is not None and date_filter == '%s-%s' % (split_date[0], split_date[1])) \
                or (label_filter is not None and (label_filter in split_label)):
            # 博客列表内容
            title_url = url_for('show_%s_markdown' % category_filter,
                                file_path=item[thumbnail.FILE_PATH].replace('markdown/%s/' % category_filter, '', 1))
            blog_list.append({'title': item[thumbnail.TITLE],
                              'title_url': title_url,
                              'content': item[thumbnail.OUTLINE],
                              'date': item[thumbnail.DATE],
                              'labels': item_labels_with_url})

    dates_with_url = []
    dates = list(dates)
    dates.sort(reverse=True)
    for date in dates:
        split_date = date.split('-')
        if len(split_date) == 2:
            new_date = split_date[0] + '年' + split_date[1] + '月'
            dates_with_url.append((new_date, url_for('show_%s_filter' % category_filter, date=date)))

    labels_with_url = []
    labels = list(labels)
    labels.sort()
    for label in labels:
        labels_with_url.append((label, url_for('show_%s_filter' % category_filter, label=label)))

    return {'outlines': blog_list, 'dates': dates_with_url, 'labels': labels_with_url}


# 博客主页
@app.route('/index.html')
def show_tab_index():
    return redirect(url_for('show_index'))


@app.route('/')
def show_index():
    app.logger.debug('show_index')
    blog_list = calc_markdown_thumbnail_list(category='tech')
    return render_template('index.html',
                           title='主页',
                           tabs=gen_tabs('tech'),
                           labels=blog_list['labels'],
                           dates=blog_list['dates'],
                           blog_list=blog_list['outlines'])


# 生活主页
@app.route('/life.html')
def show_tab_life():
    app.logger.debug('show_tab_life')
    blog_list = calc_markdown_thumbnail_list(category='life')
    return render_template('index.html',
                           title='life',
                           tabs=gen_tabs('life'),
                           labels=blog_list['labels'],
                           dates=blog_list['dates'],
                           blog_list=blog_list['outlines'])


@app.route('/tech.html')
def show_tab_tech():
    app.logger.debug('show_tab_tech')
    return render_template('tech.html')


@app.route('/about.html')
def show_tab_about():
    app.logger.debug('show_tab_about')
    return render_template('about.html')


@app.route('/markdown/tech/')
def show_tech_filter():
    app.logger.debug('show_tech_filter')
    return show_markdown_filter('tech')


@app.route('/markdown/life/')
def show_life_filter():
    app.logger.debug('show_life_filter')
    return show_markdown_filter('life')


def show_markdown_filter(category):
    date = request.args.get('date', None)
    label = request.args.get('label', None)
    app.logger.debug('show_markdown_filter category = %s; date = %s; label = %s' % (category, date, label))
    if date is None and label is None:
        return
    blog_list = calc_markdown_thumbnail_list(category=category, date=date, label=label)
    return render_template('index.html',
                           title='markdown filter',
                           tabs=gen_tabs(category),
                           labels=blog_list['labels'],
                           dates=blog_list['dates'],
                           blog_list=blog_list['outlines'])


# 博客页面
def show_markdown(file_path):
    app.logger.debug('show_markdown file_path = %s' % file_path)
    filename, suffix = os.path.splitext(file_path)
    if suffix != '.md':
        return show_static(file_path)
    f = os.path.join(INPUT_PATH, file_path).replace(os.sep, '/')
    if not os.path.exists(f) or not os.path.isfile(f):
        return page_not_found('not found [%s]', file_path)
    else:
        html_path = os.path.join(OUTPUT_PATH, '%s.html' % filename).replace(os.sep, '/')
        if not os.path.exists(html_path):
            make_markdown_html(file_path)
    thumbnail.update_hits(f)
    return app.send_static_file('%s.html' % filename)


@app.route('/tech/<file_path>')
def show_tech_markdown(file_path):
    app.logger.debug('show_tech_markdown file_path = %s' % file_path)
    return show_markdown('tech/%s' % file_path)


@app.route('/life/<file_path>')
def show_life_markdown(file_path):
    app.logger.debug('show_life_markdown file_path = %s' % file_path)
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
        upload_file.save(os.path.join(OUTPUT_PATH, secure_filename(upload_file.filename)).replace(os.sep, '/'))
        return 'congratulations, upload success.'


def check_dirs(file_path):
    file_path = file_path.replace('/', os.sep)
    if os.path.exists(file_path):
        return
    if os.path.splitext(file_path)[1] != '':
        file_path = file_path[: file_path.rfind(os.sep)]
        if os.path.exists(file_path):
            return
    os.makedirs(file_path)
    app.logger.info('make dirs(%s) success.' % file_path)


def check_static_image(file_path):
    app.logger.debug('check_static_image file_path = %s' % file_path)
    filename, suffix = os.path.splitext(file_path)
    if suffix != '.png' and suffix != '.jpg' and suffix != '.gif':
        return
    input_image_path = os.path.join(INPUT_PATH, file_path).replace(os.sep, '/')
    output_image_path = os.path.join(OUTPUT_PATH, file_path).replace(os.sep, '/')
    if not os.path.exists(input_image_path) or not os.path.isfile(input_image_path):
        return
    category = split_category(file_path)
    if category is None:
        return
    if not os.path.exists(output_image_path)\
            or os.path.getmtime(input_image_path) != os.path.getmtime(output_image_path):
        check_dirs(output_image_path)
        shutil.copyfile(input_image_path, output_image_path)
        app.logger.debug('copy image success')


@app.route('/<path:file_path>')
def show_static(file_path):
    app.logger.debug('show_static file_path = %s' % file_path)
    check_static_image(file_path)
    return app.send_static_file(file_path)


if __name__ == '__main__':
    app.run()
