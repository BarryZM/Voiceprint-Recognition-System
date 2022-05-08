# -*- coding:utf-8 -*-
# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  22:28:08.000-05:00
# Desc  : gunicorn config file

# 并行工作进程数
workers = 2
# 指定每个工作者的线程数
threads = 2

# 监听内网端口8071
bind = "0.0.0.0:8989"

# 设置非守护进程, 将进程交给supervisor管理
daemon = True
# 工作模式协程
worker_class = "gevent"
# 设置最大并发量
worker_connections = 2000
# 设置进程文件目录
pidfile = "./gunicorn.pid"
# 设置访问日志和错误信息日志路径
accesslog = "./gunicorn_acess.log"
errorlog = "./gunicorn_error.log"
# 设置日志记录水平
loglevel = "info"
