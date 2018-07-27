# -*- coding: utf-8 -*-

import os
import hashlib


def calc_file_md5(filename):
    if not os.path.isfile(filename):
        return
    if os.path.getsize(filename) > 8096:
        return _calc_large_file_md5(filename)
    return _calc_small_file_md5(filename)


def _calc_small_file_md5(filename):
    with open(filename, 'rb') as f:
        obj = hashlib.md5()
        obj.update(f.read())
        return obj.hexdigest()


def _calc_large_file_md5(filename):
    obj = hashlib.md5()
    with open(filename, 'rb') as f:
        while True:
            b = f.read(8096)
            if not b:
                break
            obj.update(b)
        return obj.hexdigest()


def fix_sep(path, sep):
    if path is None or type(path) != str:
        return path
    if sep is None or type(sep) != str or sep == '':
        return path
    if sep != '\\':
        return path.replace('\\', sep)
    if sep != '/':
        return path.replace('/', sep)
    return path


def check_dirs(file_path):
    file_path = fix_sep(file_path, os.sep)
    if os.path.exists(file_path):
        return
    if os.path.splitext(file_path)[1] != '':
        file_path = file_path[: file_path.rfind(os.sep)]
        if os.path.exists(file_path):
            return
    os.makedirs(file_path)
