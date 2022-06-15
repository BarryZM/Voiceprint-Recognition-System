# -*- coding:utf-8 -*-
# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  20:05:37.000-05:00
# Desc  : API test.

import requests


url="http://127.0.0.1:8170/score"
headers = {
    'Content-Type': 'multipart/form-data'
}

# 上传文件单独构造成以下形式
# 'file' 上传文件的字段名
# 'filename' 上传到服务器的文件名，可以和上传的文件名不同
# open('test.zip') 打开的文件对象，注意文件路径正确
# request_file = {'wav_file':(('wav_file',open('/mnt/zhaosheng/test_wav_16k/zhaosheng.wav','rb')))}
request_file = {'wav_file':open(r'/mnt/zhaosheng/test_wav_16k/zhaosheng2.wav', 'rb')}
values = {"spkid": "15151832004"}
# !不能指定header
resp = requests.request("POST",url, files=request_file, data=values)#,headers=headers)


print(resp)
print(resp.json())