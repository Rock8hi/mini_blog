# -*- coding: utf-8 -*-

from flask import Flask, url_for, redirect
from flask import request
from flask import render_template
from werkzeug.utils import secure_filename

import os
import re
import codecs
import shutil
import markdown
import math
from PIL import Image
from dbhelper import thumbnail_helper as thumbnail
from dbhelper import hits_helper as hits

import utils
import task


app = Flask(__name__)
# app.debug = True
app.debug = False

SUPPORT_PIROBOX = True
IMAGE_MAX_WIDTH = 480

thumbnail.init(app.debug)
hits.init(app.debug)

MARKDOWN_ROOT = 'markdown'
STATIC_ROOT = app.static_folder


@app.before_first_request
def before_first_request():
    app.logger.debug('before_first_request')


@app.before_request
def before_request():
    app.logger.debug('before_request')
    update_hits()


@app.errorhandler(404)
def page_not_found(error):
    app.logger.warning('page_not_found: %s' % error)
    return 'This page does not exist', 404


@app.route('/')
def show_index():
    app.logger.debug('show_index')
    blog_list = calc_markdown_thumbnail_list(category='tech')
    return render_html('主页', 'tech', blog_list['labels'], blog_list['dates'], blog_list['outlines'])


# 博客主页
@app.route('/index.html')
def show_tab_index():
    return redirect(url_for('show_index'))


# 生活主页
@app.route('/life.html')
def show_tab_life():
    app.logger.debug('show_tab_life')
    blog_list = calc_markdown_thumbnail_list(category='life')
    return render_html('生活', 'life', blog_list['labels'], blog_list['dates'], blog_list['outlines'])


@app.route('/tech.html')
def show_tab_tech():
    app.logger.debug('show_tab_tech')
    return render_template('tech.html')


@app.route('/about.html')
def show_tab_about():
    app.logger.debug('show_tab_about')
    return render_template('about.html')


@app.route('/<path:file_path>')
def show_static(file_path):
    app.logger.debug('show_static file_path = %s' % file_path)
    return check_static_image(file_path) or app.send_static_file(file_path)


@app.route('/markdown/<category>/')
def show_category_filter(category):
    app.logger.debug('show_category_filter')
    if category in ['tech', 'life'] and len(request.args) != 0:
        return show_markdown_filter(category)
    return page_not_found('category')


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
        # upload_file.save(fix_sep(os.path.join(STATIC_ROOT, secure_filename(upload_file.filename)), os.sep))
        return 'congratulations, upload success.'


def render_html(title, cur_tab, labels, dates, list_or_blog):
    blog_list = None
    blog_html = None
    if isinstance(list_or_blog, list):
        blog_list = list_or_blog
    else:
        blog_html = list_or_blog
    return render_template('index.html',
                           title=title,
                           tabs=gen_tabs(cur_tab),
                           labels=labels,
                           dates=dates,
                           support_pirobox=SUPPORT_PIROBOX,
                           blog_list=blog_list,
                           blog_html=blog_html)


def markdown_to_html(markdown_content):
    html = markdown.markdown(markdown_content, extensions=['markdown.extensions.extra',
                                                           'markdown.extensions.codehilite',
                                                           'markdown.extensions.tables',
                                                           'markdown.extensions.toc',
                                                           'markdown.extensions.fenced_code',
                                                           'markdown.extensions.smart_strong'])
    html = html.replace(r'<div class="codehilite">', r'<div class="codehilite" style="overflow-x: auto;">')
    html = re.sub(r'<img\s*(.*?)\s*/>',
                  r'<img \1 style="border: 2px solid #56d0f9; max-width: 480px; vertical-align: text-bottom;" />',
                  html)
    if SUPPORT_PIROBOX:
        # class="pirobox" or class="pirobox_gall"
        html = re.sub(r'<img\s*alt="(.*?)"\s*src="(.*?).(png|jpg|gif)"\s*style="(.*?)"\s*/>',
                      r'<a href="\2_origin.\3" rel="gallery" class="pirobox" title="\1"> '
                      r'<img src="\2.\3" alt="\1" style="\4" /> </a>',
                      html)
        # html = re.sub(r'<img\s*src="(.*?)"\s*style="(.*?)"\s*/>',
        #               r'<a href="\1" rel="gallery" class="pirobox" title=""> '
        #               r'<img src="\1" style="\3" /> </a>',
        #               html)
    return html


def update_hits():
    if request.path[:7] == '/static':
        return
    if request.path == '/favicon.ico':
        return
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
    file_path = utils.fix_sep(file_path, '/')
    split = file_path.split('/')
    return split[len(split) - 2]


def gen_tabs(category):
    return [('主页', url_for('show_index'), category == 'tech'),
            # ('技术', url_for('show_tab_tech')),
            ('生活', url_for('show_tab_life'), category == 'life'),
            # ('关于', url_for('show_tab_about'))
            ]


# 转换markdown，并将html数据写入到文件
def make_markdown_html(file_path):
    app.logger.debug('make_markdown_html file_path = %s' % file_path)
    category = split_category(file_path)
    blog_list = calc_markdown_thumbnail_list(category=category)
    # 转换markdown为html，并存入文件
    markdown_path = utils.fix_sep(os.path.join(MARKDOWN_ROOT, file_path), os.sep)
    html_path = utils.fix_sep(os.path.join(STATIC_ROOT, os.path.splitext(file_path)[0] + '.html'), os.sep)
    data = thumbnail.fetchone(utils.fix_sep(markdown_path, '/'))
    title = data[0][thumbnail.TITLE] if len(data) != 0 else '博客'
    with codecs.open(markdown_path, 'r', 'utf-8') as infile:
        utils.check_dirs(html_path)
        with codecs.open(html_path, 'w', 'utf-8', errors='xmlcharrefreplace') as outfile:
            blog_html = markdown_to_html(infile.read())
            outfile.write(render_html(title, category, blog_list['labels'], blog_list['dates'], blog_html))
            app.logger.info('convert and write "%s" success' % file_path)


def calc_markdown_thumbnail_list(**kwargs):
    category_filter = kwargs.get('category', 'tech')
    date_filter = kwargs.get('date', None)
    label_filter = kwargs.get('label', None)
    app.logger.debug('calc_markdown_thumbnail_list category_filter=%s; date_filter=%s; label_filter=%s'
                     % (category_filter, date_filter, label_filter))

    # 检测markdown文件和db上数据是否一致
    task.run()
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
                item_labels_with_url[label] = url_for('show_category_filter', category=category_filter, label=label)

        if (date_filter is None and label_filter is None) \
                or (date_filter is not None and date_filter == '%s-%s' % (split_date[0], split_date[1])) \
                or (label_filter is not None and (label_filter in split_label)):
            # 博客列表内容
            title_url = url_for('show_%s_markdown' % category_filter,
                                file_path=item[thumbnail.FILE_PATH][len('markdown/%s/' % category_filter):])
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
            dates_with_url.append((new_date, url_for('show_category_filter', category=category_filter, date=date)))

    labels_with_url = []
    labels = list(labels)
    labels.sort()
    for label in labels:
        labels_with_url.append((label, url_for('show_category_filter', category=category_filter, label=label)))

    return {'outlines': blog_list, 'dates': dates_with_url, 'labels': labels_with_url}


def show_markdown_filter(category):
    date = request.args.get('date', None)
    label = request.args.get('label', None)
    app.logger.debug('show_markdown_filter category = %s; date = %s; label = %s' % (category, date, label))
    if date is None and label is None:
        return
    blog_list = calc_markdown_thumbnail_list(category=category, date=date, label=label)
    return render_html('筛选博客列表', category, blog_list['labels'], blog_list['dates'], blog_list['outlines'])


# 博客页面
def show_markdown(file_path):
    app.logger.debug('show_markdown file_path = %s' % file_path)
    filename, suffix = os.path.splitext(file_path)
    if suffix != '.md':
        return show_static(file_path)
    markdown_path = utils.fix_sep(os.path.join(MARKDOWN_ROOT, file_path), os.sep)
    if not os.path.isfile(markdown_path):
        return page_not_found('not found [%s]', file_path)
    else:
        html_path = utils.fix_sep(os.path.join(STATIC_ROOT, '%s.html' % filename), os.sep)
        if not os.path.exists(html_path):
            make_markdown_html(file_path)
        data = thumbnail.fetchone('markdown/' + file_path)
        mtime = os.path.getmtime(markdown_path)
        if len(data) != 0 and data[0][thumbnail.MODIFIED_TIME] != mtime:
            make_markdown_html(file_path)
            thumbnail.update_modified_time('markdown/' + file_path, mtime)
    thumbnail.update_hits('markdown/' + file_path)
    return app.send_static_file('%s.html' % filename)


def check_static_image(file_path):
    app.logger.debug('check_static_image file_path = %s' % file_path)
    filename, suffix = os.path.splitext(file_path)
    if suffix != '.png' and suffix != '.jpg' and suffix != '.gif':
        return
    category = split_category(file_path)
    if category is None:
        return

    is_origin = True
    if filename[len(filename) - 7:] != '_origin':
        is_origin = False
    else:
        filename = filename[:len(filename) - 7]

    markdown_image_path = utils.fix_sep(os.path.join(MARKDOWN_ROOT, filename + suffix), os.sep)
    if not os.path.isfile(markdown_image_path):
        return

    static_image_path = utils.fix_sep(os.path.join(STATIC_ROOT, filename + suffix), os.sep)
    if not os.path.exists(static_image_path) \
            or os.path.getmtime(markdown_image_path) != os.path.getmtime(static_image_path):
        utils.check_dirs(static_image_path)
        # 从markdown目录拷贝图片到static目录，并保留原始的修改时间戳
        shutil.copy2(markdown_image_path, static_image_path)
        app.logger.debug('copy image success')

    thumb_path = '%s_thumb%s' % os.path.splitext(static_image_path)
    if not os.path.exists(thumb_path) \
            or os.path.getmtime(markdown_image_path) != os.path.getmtime(thumb_path):
        # 制作缩略图
        img = Image.open(static_image_path)
        width, height = img.size
        if width <= IMAGE_MAX_WIDTH:
            return app.send_static_file(filename + suffix)
        if os.path.exists(thumb_path):
            os.remove(thumb_path)
        rate = IMAGE_MAX_WIDTH / width
        img.thumbnail((math.floor(width * rate), math.floor(height * rate)))
        img.save(thumb_path)
        os.utime(thumb_path, (os.path.getatime(markdown_image_path), os.path.getmtime(markdown_image_path)))
        app.logger.debug('make thumb success')

    if is_origin:
        # 返回原图
        return app.send_static_file(filename + suffix)
    # 返回缩略图
    return app.send_static_file('%s_thumb%s' % (filename, suffix))


if __name__ == '__main__':
    app.run()
