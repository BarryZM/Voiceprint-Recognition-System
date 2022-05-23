from logging.handlers import RotatingFileHandler
import json
import time
import logging
import random
from flask import Flask, request, jsonify,render_template
from flask_cors import CORS
import scipy as sp
from sqlalchemy import null
import flask
import torch
import numpy as np
import pickle
import os
# SpeechBrain
from speechbrain.pretrained import SpeakerRecognition

from datetime import datetime, timedelta

# utils
from utils.database import add_to_database
from utils.save import save_wav_from_url,save_wav_from_file,save_embedding
from utils.preprocess import self_test,vad_and_upsample
from utils.scores import get_scores
from utils.query import check_new_record

import socketio
# config file
import cfg

# websocket connection
from geventwebsocket.handler import WebSocketHandler         #提供WS（websocket）协议处理
from geventwebsocket.server import WSGIServer                #websocket服务承载
#WSGIServer导入的就是gevent.pywsgi中的类
# from gevent.pywsgi import WSGIServer
from geventwebsocket.websocket import WebSocket              #websocket语法提示

import json
import sys
import os
from flask_sockets import Sockets
import time
from gevent import monkey
from flask import Flask
from gevent import pywsgi
from geventwebsocket.handler import WebSocketHandler

# sys.path.append(os.path.abspath(os.path.dirname(__file__) + '/' + '..'))
# sys.path.append("..")
# monkey.patch_all()

from datetime import datetime
from flask_apscheduler import APScheduler

scheduler = APScheduler()
ws_dict={}
# cosine
similarity = torch.nn.CosineSimilarity(dim=-1, eps=1e-6)

# embedding model
spkreg = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", savedir="/mnt/zhaosheng/brain/notebooks/pretrained_ecapa")

client_list = []

# log
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "[%(asctime)s]  %(levelname)s  [%(filename)s]  #%(lineno)d <%(process)d:%(thread)d>  %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]",
)
handler = RotatingFileHandler(
    "./vvs_server.log", maxBytes=20 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
handler.setFormatter(formatter)
handler.namer = lambda x: "vvs_server." + x.split(".")[-1]
logger.addHandler(handler)

# app 
from flask_sock import Sock

app = Flask(__name__)
sock = Sock(app)

# app = Flask(__name__)

class Config(object):
    JOBS = [
        {
            'id': 'job1',
            'func': 'vvs_service:task',
            'args': (1, 2),
            'trigger': 'interval',
            'seconds': 10
        }
    ]
    SCHEDULER_API_ENABLED = True

pre_timestamp = ""
def task(a, b):
    pass
    # # 定时任务，自动注册
    # print("开始自动注册")
    # pre_timestamp = (datetime.now() + timedelta(minutes=-5)).strftime("%Y-%m-%d %H:%M:%S")
    # now_timestamp = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    # result = check_new_record(pre_timestamp,now_timestamp)
    # print(len(result))
    # print(result[0])
    # for item in result:
    #     record_file_name= item["record_file_name"]
    #     caller_num= item["caller_num"]
    #     url = f"http://116.62.120.233/mpccApi/common/downloadFile.json?type=0&addr={record_file_name}"
    #     filename = record_file_name.split("/")[-1]
    #     save_path = f"root/{caller_num}/{filename}"

    #     print(f"Registering:\n\t-> URL {url}\n\t-> SPKID {caller_num}\n\t-> Save Path {save_path}")

    # print(str(datetime.datetime.now()) + ' execute task ' + '{}+{}={}'.format(a, b, a + b))

# app = Flask(__name__)
CORS(app, supports_credentials=True,
        origins="*", methods="*", allow_headers="*")

# sockets = Sockets(app)
now = time.strftime('%Y-%m-%d-%H-%M-%S', time.localtime(time.time()))


logger.info("\tLoad blacklist files ... ")
with open(cfg.BLACK_LIST, 'rb') as base:
    black_database = pickle.load(base)


@app.route("/", methods=["GET"])
def index():
    spks = list(black_database.keys())
    
    spks_num = len(spks)
    kwargs = {
        "spks_num": spks_num,
        "spks":spks
    }

    return render_template('index.html',**kwargs)

@app.route('/websocket')
def websocket():
    client_socket = request.environ.get('wsgi.websocket')  # type:WebSocket
    client_list.append(client_socket)
    # print(len(client_list), client_list)
    while 1:
        msg_from_cli = client_socket.receive()
        # print(msg_from_cli)
        #收到任何一个客户端的信息都进行全部转发（注意如果某个客户端连接断开，在遍历发送时连接不存在会报错，需要异常处理）
        for client in client_list:
            try:
                client.send(msg_from_cli)
            except Exception as e:
                continue
            
@app.route('/info', methods=["GET","POST"])
def getInfo():
    client_socket=request.environ.get('wsgi.websocket')
    print(client_socket)
    client_list.append(client_socket)
    while 1:
        time.sleep(5)
        # msg_from_cli = client_socket.receive()
        # print(msg_from_cli)
        names_inbase = list(black_database.keys())
        number = len(names_inbase)
        
        response = {
            "code": 2000,
            "status": "success",
            "number": number,
            "err_msg": "null"
        }


        # 收到任何一个客户端的信息都进行全部转发（注意如果某个客户端连接断开，在遍历发送时连接不存在会报错，需要异常处理）
        for client in client_list:
            try:
                client.send(response)
                print(number)
            except Exception as e:
                print(e)

@app.route("/test/<test_type>", methods=["POST","GET"])
def test(test_type):
    if request.method == "GET":
        if test_type == "file":
            return render_template('score_from_file.html')
        elif test_type == "url":
            return render_template('score_from_url.html')
    if request.method == "POST":
        names_inbase = black_database.keys()
        logger.info("@ -> Test")
        logger.info(f"\tBlack spk number: {len(names_inbase)}")
        

        # get request.files
        new_spkid = flask.request.form.get("spkid")


        if test_type == "file":
            new_file = request.files["wav_file"]
            filepath,speech_number = save_wav_from_file(new_file,new_spkid,os.path.join(cfg.SAVE_PATH,"raw"))
        elif test_type == "url":
            new_url =request.form.get("wav_url")
            filepath,speech_number = save_wav_from_url(new_url,new_spkid,os.path.join(cfg.SAVE_PATH,"raw"))
        start_time = time.time()
        # Preprocess: vad + upsample to 16k + self test
        wav,before_vad_length,after_vad_length = vad_and_upsample(filepath,savepath=os.path.join(cfg.SAVE_PATH,"preprocessed"),spkid=new_spkid)
        pass_test, msg = self_test(wav, spkreg,similarity, sr=16000, split_num=cfg.TEST_SPLIT_NUM, min_length=cfg.MIN_LENGTH, similarity_limit=cfg.SELF_TEST_TH)
        if not pass_test:
            response = {
                "code": 2000,
                "status": "error",
                "err_msg": msg
            }
            end_time = time.time()
            time_used = end_time - start_time
            logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
            logger.info(f"\t# Error: {msg}s")
            return json.dumps(response, ensure_ascii=False)

        embedding = spkreg.encode_batch(wav)[0][0]

        scores,top_list = get_scores(black_database,embedding,cfg.BLACK_TH,similarity,top_num=10)

        end_time = time.time()
        time_used = end_time - start_time
        logger.info(f"\t# Success: {msg}")
        logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
        response = {
            "code": 2000,
            "status": "success",
            "scores": scores,
            "err_msg": "null",
            "raw_length":before_vad_length,
            "vad_length":after_vad_length,
            "top_list":top_list
        }
        print(response)
        return json.dumps(response, ensure_ascii=False)

@app.route("/namelist", methods=["GET"])
def namelist():
    if request.method == "GET":
        start_time = time.time()
        names_inbase = list(black_database.keys())
        numbers = len(names_inbase)
        logger.info("@ -> NameList")
        logger.info(f"\tBlack spk number: {len(names_inbase)}")
        end_time = time.time()
        time_used = end_time - start_time
        logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
        response = {
            "code": 2000,
            "status": "success",
            "names": names_inbase,
            "names_10": names_inbase[-10:],
            "numbers": numbers,
            "err_msg": "null"
        }
        print(response)
        return json.dumps(response, ensure_ascii=False)

@app.route("/register/<register_type>", methods=["POST","GET"])
def register(register_type):
    if request.method == "GET":
        if register_type == "file":
            return render_template('register_from_file.html')
        elif register_type == "url":
            return render_template('register_from_url.html')

    
    if request.method == "POST":  
        names_inbase = black_database.keys()
        logger.info("# => Register")
        logger.info(f"\tBlack spk number: {len(names_inbase)}")
        

        # get request.files
        new_spkid = request.form.get("spkid")
        
        
        if register_type == "file":
            new_file = request.files["wav_file"]
            filepath,speech_number = save_wav_from_file(new_file,new_spkid,os.path.join(cfg.BASE_WAV_PATH,"raw"))
        elif register_type == "url":
            new_url =request.form.get("wav_url")
            filepath,speech_number = save_wav_from_url(new_url,new_spkid,os.path.join(cfg.BASE_WAV_PATH,"raw"))
        start_time = time.time()
        # Preprocess: vad + upsample to 16k + self test
        wav,before_vad_length,after_vad_length = vad_and_upsample(filepath,savepath=os.path.join(cfg.BASE_WAV_PATH,"preprocessed"),spkid=new_spkid)
        pass_test, msg = self_test(wav, spkreg,similarity, sr=16000, split_num=cfg.TEST_SPLIT_NUM, min_length=cfg.MIN_LENGTH, similarity_limit=cfg.SELF_TEST_TH)
        if not pass_test:
            response = {
                "code": 2000,
                "status": "error",
                "err_msg": msg
            }
            end_time = time.time()
            time_used = end_time - start_time
            logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
            logger.info(f"\t# Error: {msg}")
            return json.dumps(response, ensure_ascii=False)

        embedding = spkreg.encode_batch(wav)[0][0]
        add_success = add_to_database(database=black_database,embedding=embedding,spkid=new_spkid,wav_file_path=filepath,database_filepath=cfg.BLACK_LIST)
        if not add_success:
            response = {
                "code": 2000,
                "status": "error",
                "err_msg": "Already in database!"
            }
            end_time = time.time()
            time_used = end_time - start_time
            logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
            logger.info(f"\t# Error: Already in database!")
            return json.dumps(response, ensure_ascii=False)
        else:
            logger.info(f"\t# Msg: Save to dabase success.")
        end_time = time.time()
        time_used = end_time - start_time
        logger.info(f"\t# Success: {msg}")
        logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
        response = {
            "code": 2000,
            "status": "success",
            "raw_length":before_vad_length,
            "vad_length":after_vad_length,
            "err_msg": "null"
        }
        #return redirect(url_for('login'))

        return json.dumps(response, ensure_ascii=False)

@app.route("/conn_ws")
def ws_app():
    print("开始建立ws链接")
    user_socket = request.environ.get("wsgi.websocket")
    print(user_socket, "连接已经建立了")
    while True:
        msg = user_socket.receive()
        print(msg)
        user_socket.send(msg)
        print(user_socket)
    return "200 okkk"

@sock.route('/echo')
def echo(sock):
    while True:
        
        data = sock.receive()
        print(data)
        
        while True:
            
            time.sleep(3)
            names_10 = list(black_database.keys())[-10:]
            
            number = len(black_database.keys())
            response = {
                "code": 2000,
                "status": "success",
                "number": number,
                "names_10":names_10,
                "err_msg": "null"
            }
            sock.send(json.dumps(response, ensure_ascii=False))


if __name__ == "__main__":
    # http_server = WSGIServer(('127.0.0.1', 8170), application=app, handler_class=WebSocketHandler)
    # http_server.serve_forever()
    app.config.from_object(Config())
    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()
    # sockets = Sockets(app)

    app.run(host='127.0.0.1', threaded=True, port=8170, debug=True,)
    # host="0.0.0.0"

    # server = pywsgi.WSGIServer(('127.0.0.1', 8170), app, handler_class=WebSocketHandler)
    # print('server start')
    # server.serve_forever()

    # from gevent import pywsgi
    # from geventwebsocket.handler import WebSocketHandler
    # server = pywsgi.WSGIServer(('127.0.0.1', 8170), app, handler_class=WebSocketHandler)
    # logging.info('server start')
    # server.serve_forever()

    # http_serv=WSGIServer(("127.0.0.1",8170),app,handler_class=WebSocketHandler)
    # http_serv.serve_forever()

    # socketio.run(app, debug=True,host='127.0.0.1',port=8170)