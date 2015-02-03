# deny-demo
deny轻量级的web框架Demo 只需一个文件


python的micro web框架 Deny,只需要在项目目录中包含一个deny.py文件
 你就拥有了一个超级简洁的web框架，其实阅读deny.py源码你会发现，代码中
 只有解密和解压if 0:__source__=\的加密压缩字符，然后创建它的temp文件,
 window中查看用户临时文件目录会有一个“denied_uframework”开头的文件夹，
 其中包含jinja2、werkzeuge、simplejson等模块，并将它们加入到sys.path中，
 想法真的十分巧妙。
