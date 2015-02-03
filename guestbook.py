#! usr/bin/env python
# -*- coding: UTF-8 -*-
from deny import parse_json, render_template, request,\
    redirect, url_for, dump_json, route, run
'''
 python的micro web框架 Deny,只需要在项目目录中包含一个deny.py文件
 你就拥有了一个超级简洁的web框架，其实阅读deny.py源码你会发现，代码中
 只有解密和解压if 0:__source__=\的加密压缩字符，然后创建它的temp文件,
 window中查看用户临时文件目录会有一个“denied_uframework”开头的文件夹，
 其中包含jinja2、werkzeuge、simplejson等模块，并将它们加入到sys.path中，
 想法真的十分巧妙。
'''

database = 'guestbook.txt'


def get_all_notes():
    f = open(database)
    try:
        return map(parse_json, f)
    finally:
        f.close()


def add_note(title, text):
    f = open(database, 'a')
    try:
        f.write('%s\n' % dump_json(dict(
            title=title,
            text=text
        )))
    finally:
        f.close()


@route('/')
def show_notes():
    return render_template(notes=get_all_notes())


@route('/create')
def create_note():
    add_note(request.values['title'],
             request.values['text'])
    return redirect(url_for('show_notes'))


if __name__ == '__main__':
    run()
