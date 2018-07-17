#!/root/blog/flask/venv/bin/python
# -*- coding: utf-8

from dbhelper import sqlite3_helper as helper


DB_FILE_PATH = 'mini_blog.db'

ID = 0
IP = 1
URL = 2
COUNT = 3


def check_table():
    sql = '''CREATE TABLE IF NOT EXISTS `hits` (
                                        `id` INTEGER PRIMARY KEY AUTOINCREMENT,
                                        `ip` varchar(16) NOT NULL,
                                        `url` varchar(256) NOT NULL,
                                        `time` datetime NOT NULL);'''
    conn = helper.get_conn(DB_FILE_PATH)
    helper.create_table(conn, sql)


def fetchall():
    sql = '''SELECT * FROM `hits`'''
    conn = helper.get_conn(DB_FILE_PATH)
    return helper.fetchall(conn, sql)


def fetchone(ip):
    sql = '''SELECT * FROM `hits` WHERE `ip` = ?;'''
    conn = helper.get_conn(DB_FILE_PATH)
    return helper.fetchone(conn, sql, ip)


def save(ip, url):
    data = (ip, url)
    insert([data])


def insert(data):
    sql = '''INSERT INTO `hits` (`ip`, `url`, `time`) VALUES (?, ?, datetime('now', 'localtime'))'''
    conn = helper.get_conn(DB_FILE_PATH)
    helper.save(conn, sql, data)


def init(debug=False):
    helper.SHOW_SQL = debug
    check_table()


def test():
    global DB_FILE_PATH
    DB_FILE_PATH = 'test.db'
    init(True)
    insert([('123.123.123.456', 'abc/def/hell.html'), ('123.789.123.456', 'TTT/FFF/hell.html')])
    print('fetchall:')
    for k in fetchall():
        print(k)


if __name__ == '__main__':
    test()
