#!/root/blog/flask/venv/bin/python
# -*- coding: utf-8

from dbhelper import sqlite3_helper as helper


DB_FILE_PATH = 'mini_blog.db'

ID = 0
CATEGORY = 1
TITLE = 2
DATE = 3
LABEL = 4
OUTLINE = 5
FILE_PATH = 6
FILE_MD5 = 7
MODIFIED_TIME = 8
HTML_PATH = 9
READ_COUNT = 10


def check_table():
    sql = '''CREATE TABLE IF NOT EXISTS `markdown_thumbnail` (
                                        `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                                        `category` varchar(32) NOT NULL,
                                        `title` varchar(128) NOT NULL,
                                        `date` varchar(64) NOT NULL,
                                        `label` varchar(128) NOT NULL,
                                        `outline` varchar(1024) NOT NULL,
                                        `file_path` varchar(256) NOT NULL,
                                        `file_md5` varchar(32) NOT NULL,
                                        `modified_time` varchar(32) NOT NULL,
                                        `html_path` varchar(256) NOT NULL,
                                        `hits` int NOT NULL);'''
    conn = helper.get_conn(DB_FILE_PATH)
    helper.create_table(conn, sql)


def save(data_list):
    if data_list is None:
        return
    if not isinstance(data_list, list):
        return
    if len(data_list) == 0:
        return
    sql = '''INSERT INTO `markdown_thumbnail` (`category`, `title`, `date`, `label`, `outline`, `file_path`,
            `file_md5`, `modified_time`, `html_path`, `hits`) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)'''

    conn = helper.get_conn(DB_FILE_PATH)
    helper.save(conn, sql, data_list)


def fetchall():
    sql = '''SELECT * FROM `markdown_thumbnail`'''
    conn = helper.get_conn(DB_FILE_PATH)
    return helper.fetchall(conn, sql)


def fetchone(file_path):
    sql = '''SELECT * FROM `markdown_thumbnail` WHERE `file_path` = ? LIMIT 1;'''
    conn = helper.get_conn(DB_FILE_PATH)
    return helper.fetchone(conn, sql, file_path)


def fetchgroup(category):
    sql = '''SELECT * FROM `markdown_thumbnail` WHERE `category` = ?;'''
    conn = helper.get_conn(DB_FILE_PATH)
    return helper.fetchone(conn, sql, category)


def update_thumbnail(data_list):
    if data_list is None:
        return
    if not isinstance(data_list, list):
        return
    if len(data_list) == 0:
        return
    sql = '''UPDATE `markdown_thumbnail` SET `title` = ?, `date` = ?, `label` = ?,
                     `outline` = ?, `file_md5` = ?, `modified_time` = ? WHERE `file_path` = ?;'''

    conn = helper.get_conn(DB_FILE_PATH)
    helper.update(conn, sql, data_list)


def update_hits(file_path, count=1):
    sql = '''UPDATE `markdown_thumbnail` SET `hits` = `hits` + ? WHERE `file_path` = ?;'''

    conn = helper.get_conn(DB_FILE_PATH)
    helper.update(conn, sql, [(count, file_path)])


def init(debug=False):
    helper.SHOW_SQL = debug
    check_table()


def test():
    global DB_FILE_PATH
    DB_FILE_PATH = 'test.db'
    init(True)
    data = [('tech', 'title ss', '2018-09-08', 'android,python', 'sadflk lji ', 'abc/wdd/wed/bb.md', 'aaaaasssssdddddfffffggggghhhhhjj', '2018-07-01', 'abc/wed/bb.md', 124),
            ('tech', 'title ss', '2018-09-08', 'android,python', 'sadflk lji ', 'abc/wdd/wed/aa.md', 'aaaaasssssdddddfffffggggghhhhhjj', '2018-07-01', 'abc/wed/bb.md', 124),
            ('tech', 'title ss', '2018-09-08', 'android,python', 'sadflk lji ', 'abc/wdd/wed/ff.md', 'aaaaasssssdddddfffffggggghhhhhjj', '2018-07-01', 'abc/wed/bb.md', 124),
            ('tech', 'title ss', '2018-09-08', 'android,python', 'sadflk lji ', 'abc/wdd/wed/gg.md', 'aaaaasssssdddddfffffggggghhhhhjj', '2018-07-01', 'abc/wed/bb.md', 124)]
    save(data)
    data = [('title ss', '2018-09-08', 'android,python', 'sadflk lji ', 'aaaaasssssdddddfffffggggghhhhhcc', '2018-07-01', 'abc/wdd/wed/bb.md'),
            ('title ss', '2018-09-08', 'android,python', 'sadflk lji ', 'aaaaasssssdddddfffffggggghhhhhww', '2018-07-01', 'abc/wdd/wed/aa.md'),
            ('title ss', '2018-09-08', 'android,python', 'sadflk lji ', 'aaaaasssssdddddfffffggggghhhhhxx', '2018-07-01', 'abc/wdd/wed/ff.md'),
            ('title ss', '2018-09-08', 'android,python', 'sadflk lji ', 'aaaaasssssdddddfffffggggghhhhhzz', '2018-07-01', 'abc/wdd/wed/gg.md')]
    update_thumbnail(data)
    update_hits('abc/wdd/wed/bb.md')
    print('fetchall:')
    for k in fetchall():
        print(k)
    print('fetchone:')
    for k in fetchone('abc/wdd/wed/gg.md'):
        print(k)
    print('fetchgroup:')
    for k in fetchgroup('tech'):
        print(k)


if __name__ == '__main__':
    test()
