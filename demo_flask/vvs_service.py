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



# utils
from utils.database import add_to_database
from utils.save import save_wav_from_url,save_wav_from_file
from utils.preprocess import self_test,vad_and_upsample
from utils.scores import get_scores,self_check


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


from datetime import datetime
from flask_apscheduler import APScheduler

scheduler = APScheduler()

# 初始化
client_list = []
ws_dict={}
today_right = 0 # 今日注册且正确人数
today_total = 0 # 今日注册人数

# cosine
similarity = torch.nn.CosineSimilarity(dim=-1, eps=1e-6)

# embedding model
spkreg = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", savedir="/mnt/zhaosheng/brain/notebooks/pretrained_ecapa")

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

CORS(app, supports_credentials=True,
        origins="*", methods="*", allow_headers="*")


# Load blackbase
logger.info("\tLoad blacklist files ... ")
if os.path.exists(cfg.BLACK_LIST):
    with open(cfg.BLACK_LIST, 'rb') as base:
        black_database = pickle.load(base)
    logger.info("\tLoad blacklist success!")
else:
    black_database = {}
    logger.info(f"\tLoad blacklist Error! No such file:{cfg.BLACK_LIST}")


# 主页
@app.route("/", methods=["GET"])
def index():
    spks = list(black_database.keys())
    spks_num = len(spks)
    kwargs = {
        "spks_num": spks_num,
        "spks":spks
    }
    return render_template('index.html',**kwargs)

# Websocket实时更新注册人数等信息         
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

# 声纹对比模块
@app.route("/test/<test_type>", methods=["POST","GET"])
def test(test_type):
    if request.method == "GET":
        if test_type == "file":
            return render_template('score_from_file.html')
        elif test_type == "url":
            return render_template('score_from_url.html')
    if request.method == "POST":
        # get request.files
        new_spkid = flask.request.form.get("spkid")
        names_inbase = black_database.keys()
        logger.info("@ -> Test {new_spkid}")
        logger.info(f"\tBlack spk number: {len(names_inbase)}")
        
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
        
        scores,top_list = get_scores(black_database,
                                    embedding,
                                    cfg.BLACK_TH,
                                    similarity,
                                    top_num=10)

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

# 声纹库信息获取
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

# 声纹注册模块
@app.route("/register/<register_type>", methods=["POST","GET"])
def register(register_type):
    if request.method == "GET":
        if register_type == "file":
            return render_template('register_from_file.html')
        elif register_type == "url":
            return render_template('register_from_url.html')

    if request.method == "POST":
        


        global today_right
        global today_total
        global black_database
        names_inbase = black_database.keys()
        logger.info("# => Register")
        logger.info(f"\tBlack spk number: {len(names_inbase)}")
        

        # get request.files
        new_spkid = request.form.get("spkid")

        # # 判断说话人文件是否已经存在
        # if os.path.exists("./base_wavs/raw/{new_spkid}"):
        #     print(e)
        #     response = {
        #         "code": 2000,
        #         "status": "error",
        #         "err_msg": ""
        #     }
        #     end_time = time.time()
        #     time_used = end_time - start_time
        #     logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
        #     logger.info(f"\t# Error: 文件大小检验失败")
        #     return json.dumps(response, ensure_ascii=False)
        
        
        if register_type == "file":
            new_file = request.files["wav_file"]
            filepath,speech_number = save_wav_from_file(new_file,new_spkid,os.path.join(cfg.BASE_WAV_PATH,"raw"))
        elif register_type == "url":
            new_url =request.form.get("wav_url")
            filepath,speech_number = save_wav_from_url(new_url,new_spkid,os.path.join(cfg.BASE_WAV_PATH,"raw"))
        start_time = time.time()
        # Preprocess: vad + upsample to 16k + self test
        try:
            wav,before_vad_length,after_vad_length,preprocessed_filepath = vad_and_upsample(filepath,savepath=os.path.join(cfg.BASE_WAV_PATH,"preprocessed"),spkid=new_spkid)
        except Exception as e:
            print(e)
            response = {
                "code": 2000,
                "status": "error",
                "err_msg": str(e)
            }
            end_time = time.time()
            time_used = end_time - start_time
            logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
            logger.info(f"\t# Error: 文件大小检验失败")
            return json.dumps(response, ensure_ascii=False)
            # # !todo 文件大小检验，错误提示返回
            # print(f"File error")
            # return
        pass_test, msg,max_score,mean_score,min_score = self_test(wav, spkreg,similarity, sr=16000, split_num=cfg.TEST_SPLIT_NUM, min_length=cfg.MIN_LENGTH, similarity_limit=cfg.SELF_TEST_TH)
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
        
        if len(black_database.keys()) > 1:
            if cfg.AUTO_TESTING_MODE:
                logger.info(f"\t# Self pre-test!")
                predict_right = self_check(database=black_database,
                                            embedding=embedding,
                                            spkid=new_spkid,
                                            black_limit=cfg.BLACK_TH,
                                            similarity=similarity,
                                            top_num=10)
                if predict_right:
                    today_right += 1
                    logger.info(f"\t# Self pre-test pass √")
                else:
                    logger.info(f"\t# Self pre-test error !")
                today_total += 1

        add_success = add_to_database(database=black_database,
                                        embedding=embedding,
                                        spkid=new_spkid,
                                        wav_file_path=preprocessed_filepath,
                                        raw_file_path=filepath,
                                        database_filepath=cfg.BLACK_LIST,
                                        max_score=max_score,
                                        mean_score=mean_score,
                                        min_score=min_score)
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

# websocket test
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

# Websocket实时更新注册人数等信息   
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
    app.run(host='127.0.0.1', threaded=False, port=8170, debug=True,)