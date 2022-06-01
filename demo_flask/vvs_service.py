from email.policy import default
from hashlib import new
from logging.handlers import RotatingFileHandler
import json
from platform import python_version_tuple
import time
import logging
from flask import Flask, request, jsonify,render_template
from flask_cors import CORS
import flask
import torch
import numpy as np
import pickle
import os
from datetime import datetime

# SpeechBrain
from speechbrain.pretrained import SpeakerRecognition

# utils
from utils.database import add_to_database
from utils.save import save_wav_from_url,save_wav_from_file
from utils.preprocess import self_test,vad_and_upsample
from utils.scores import get_scores,self_check
from utils.orm import init_info,add_hit,add_register,add_self_test,add_right,add_test,add_error,add_speaker,add_log
from utils.phone import getPhoneInfo
from utils.query import query_speaker,query_hit_phone,query_hit_location,query_database_info,query_date_info,check_url_already_exists,add_to_log
# config file
import cfg

# websocket
import socketio
from flask_sockets import Sockets
from geventwebsocket.handler import WebSocketHandler

# 初始化
# 数据库
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import desc
from sqlalchemy import func
app=Flask(__name__)
#配置数据库的连接用户,启动地址端口号数据库名
app.config["SQLALCHEMY_DATABASE_URI"]="mysql://root:Nt3380518!zhaosheng123@zhaosheng.mysql.rds.aliyuncs.com:27546/si"
# server=zhaosheng.mysql.rds.aliyuncs.com;port=27546;user=root;password=Nt3380518!zhaosheng123;database=shuadan;Charset=utf8;
# 设置是否追踪数据库的增删改查，会有显著的开销，一般设置为False
app.config["SQLALCHEMY_TRACK_MOD/IFICATIONS"]=False
# 创建SQLAlchemy对象，，并与当前数据库关联，TCP连接
db=SQLAlchemy(app)

class Info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date=db.Column(db.String(20))                       # 日期字符串
    test = db.Column(db.Integer,default=0)              # 成功测试次数
    self_test = db.Column(db.Integer,default=0)         # 自我测试次数
    register = db.Column(db.Integer,default=0)          # 成功注册次数
    right = db.Column(db.Integer,default=0)             # 自我测试且正确次数
    hit = db.Column(db.Integer,default=0)               # 今日测试过程命中次数
    register_error_1 = db.Column(db.Integer,default=0)  # 注册自我检验不合格次数
    register_error_2 = db.Column(db.Integer,default=0)  # 注册时长不合格
    register_error_3 = db.Column(db.Integer,default=0)  # 注册文件错误
    test_error_1 = db.Column(db.Integer,default=0)      # 测试自我检验不合格次数
    test_error_2 = db.Column(db.Integer,default=0)      # 测试时长不合格
    test_error_3 = db.Column(db.Integer,default=0)      # 测试文件错误

class Speaker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10),default="none")
    file_url = db.Column(db.String(256))
    phone = db.Column(db.String(12))
    register_time = db.Column(db.DateTime, default=datetime.now)
    province = db.Column(db.String(10))
    city = db.Column(db.String(10))
    phone_type = db.Column(db.String(10))
    area_code = db.Column(db.String(10))
    zip_code = db.Column(db.String(10))
    self_test_score_mean = db.Column(db.Float(8),default=0.0)
    self_test_score_min = db.Column(db.Float(8),default=0.0)
    self_test_score_max = db.Column(db.Float(8),default=0.0)
    call_begintime = db.Column(db.DateTime)
    call_endtime = db.Column(db.DateTime)
    status = db.Column(db.Integer(),default=1)                          # 0.未激活  1.激活
    class_number = db.Column(db.Integer())                    # 声纹预分类的类别

class Log(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    phone = db.Column(db.String(20))
    time = db.Column(db.DateTime, default=datetime.now)
    action_type = db.Column(db.Integer(),default=0) # test:1 # register:2 # self_test:3 # hit:4
    err_type = db.Column(db.Integer(),default=0)    # test:{0:一切正常 1:质量不合格 2:长度不合格  3: 其他错误} register:{0:一切正常 1:质量不合格 2:长度不合格  3: 其他错误}  self_test:{1:TP在黑库中且正确 2:FP1在黑库中但错误(未命中) 3:FP2在黑库中但错误(错误判断其不在黑库中)  4:TN不在黑库中且正确  5:FN 不在黑库中且错误}
    file_url = db.Column(db.String(256),default="")
    message = db.Column(db.String(128))

client_list = []
ws_dict={}

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

# HomePage
@app.route("/", methods=["GET"])
def index():
    spks = list(black_database.keys())
    spks_num = len(spks)
    kwargs = {
        "spks_num": spks_num,
        "spks":spks
    }
    return render_template('index.html',**kwargs)

# Test
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
            if "duration" in msg:
                add_to_log(phone=new_spkid, action_type=1, err_type=2, message=f"{msg}")
            else:
                add_to_log(phone=new_spkid, action_type=2, err_type=2, message=f"{msg}")
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
        add_to_log(phone=new_spkid, action_type=1, err_type=0, message=f"")
        if scores["inbase"] == 1:
            add_to_log(phone=new_spkid, action_type=4, err_type=1, message=f"对比命中：{top_list}")
        else:
            add_to_log(phone=new_spkid, action_type=4, err_type=0, message=f"对比未命中：{top_list}")

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

# Register
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
        new_spkid = request.form["spkid"]
        call_begintime = request.form["call_begintime"]
        call_endtime = request.form["call_endtime"]
        
        if register_type == "file":
            new_file = request.files["wav_file"]
            filepath,speech_number = save_wav_from_file(new_file,new_spkid,os.path.join(cfg.BASE_WAV_PATH,"raw"))
        elif register_type == "url":
            new_url =request.form.get("wav_url")
            # TODO 判断new_url 是否已存在：
            if check_url_already_exists(new_url):
                response = {
                    "code": 2000,
                    "status": "error",
                    "err_msg": str("已注册过该音频")
                    }
                logger.info(f"\t# Error:已注册过该音频")
                return json.dumps(response, ensure_ascii=False)
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
            logger.info(f"\t# Error: 文件读取失败")
            add_to_log(phone=new_spkid, action_type=2, err_type=3, message=f"文件读取失败")
            return json.dumps(response, ensure_ascii=False)

        pass_test, msg,max_score,mean_score,min_score = self_test(wav, spkreg,similarity, sr=16000, split_num=cfg.TEST_SPLIT_NUM, min_length=cfg.MIN_LENGTH, similarity_limit=cfg.SELF_TEST_TH)
        
        if not pass_test:
            response = {
                "code": 2000,
                "status": "error",
                "err_msg": msg
            }
            if "duration" in msg:
                add_to_log(phone=new_spkid, action_type=2, err_type=2, message=f"{msg}")
            else:
                add_to_log(phone=new_spkid, action_type=2, err_type=1, message=f"{msg}")
            end_time = time.time()
            time_used = end_time - start_time
            logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
            logger.info(f"\t# Error: {msg}")
            return json.dumps(response, ensure_ascii=False)

        embedding = spkreg.encode_batch(wav)[0][0]
        
        #TODO:预分类模块
        max_class_score = 0
        max_class_index = 0
        for index,i in enumerate(torch.eye(192)):
            now_class_score = similarity(embedding,i)
            if now_class_score>max_class_score:
                max_class_score=now_class_score
                max_class_index = index
        




        if len(black_database.keys()) > 1:
            if cfg.AUTO_TESTING_MODE:
                predict_right,status,pre_test_msg = self_check(database=black_database,
                                            embedding=embedding,
                                            spkid=new_spkid,
                                            black_limit=cfg.BLACK_TH,
                                            similarity=similarity,
                                            top_num=10)               
                add_self_test(db,Info)
                add_to_log(phone=new_spkid, action_type=3, err_type=status, message=f"{pre_test_msg}")
                if predict_right:
                    
                    logger.info(f"\t# Pre-test pass √")
                    logger.info(f"\t# Pre-test msg:{pre_test_msg}")
                    
                    add_right(db,Info)
                    add_hit(db,Info)
                    phone_info = getPhoneInfo(new_spkid)
                    if phone_info == None:
                        phone_info = {}
                    log_info ={
                        "city":phone_info.get("city",None),
                        "province":phone_info.get("province",None),
                        "phone_type":phone_info.get("phone_type",None),
                        "hit_time":datetime.now(),
                        "phone":new_spkid
                    }
                    # add_log(log_info,db,Log)
                else:
                    logger.info(f"\t# Pre-test error !")
                    logger.info(f"\t# Pre-test msg:{pre_test_msg}")
                


        add_success,phone_info = add_to_database(database=black_database,
                                        embedding=embedding,
                                        spkid=new_spkid,
                                        wav_file_path=preprocessed_filepath,
                                        raw_file_path=filepath,
                                        database_filepath=cfg.BLACK_LIST,
                                        max_score=max_score,
                                        mean_score=mean_score,
                                        min_score=min_score,
                                        max_class_index=max_class_index)
        if not add_success:
            response = {
                "code": 2000,
                "status": "error",
                "err_msg": "Already in database!"
            }
            end_time = time.time()
            time_used = end_time - start_time
            logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
            logger.info(f"\t# Error: Already in database! Skipped!")
            return json.dumps(response, ensure_ascii=False)
        else:
            logger.info(f"\t# Msg: Save to dabase success, class:{max_class_index}")
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

        skp_info = {
            "name":"none",
            "phone":new_spkid,
            "uuid":new_url,
            "hit":0,
            "register_time":datetime.now(),
            "province":phone_info.get("province",None),
            "city":phone_info.get("city",None),
            "phone_type":phone_info.get("phone_type",None),
            "area_code":phone_info.get("area_code",None),
            "zip_code":phone_info.get("zip_code",None),
            "self_test_score_mean":mean_score.numpy(),
            "self_test_score_min":min_score.numpy(),
            "self_test_score_max":max_score.numpy(),
            "call_begintime":call_begintime,
            "call_endtime":call_endtime,
            "max_class_index":max_class_index
        }
        add_speaker(skp_info,db,Speaker)
        print("register info add to msyql")
        add_to_log(phone=new_spkid, action_type=2, err_type=0, message=f"{msg}")
        return json.dumps(response, ensure_ascii=False)

# Websockets
@sock.route('/namelist_ws')
def namelist_ws(sock):
    while True:
        sock.send(query_speaker())
        time.sleep(3)

@sock.route('/hit_phone_info_ws')
def hit_phone_info_ws(sock):
    while True:
        sock.send(query_hit_phone())
        time.sleep(3)

@sock.route('/hit_info_ws')
def hit_info_ws(sock):
    while True:
        sock.send(query_hit_location())
        time.sleep(3)
 
@sock.route('/database_info_ws')
def database_info_ws(sock):
    while True:
        sock.send(query_database_info())
        time.sleep(3)

@sock.route('/date_info_ws')
def date_info_ws(sock):
    while True:
        date = time.strftime("%Y%m%d",time.localtime(time.time()))
        sock.send(query_date_info(date))
        time.sleep(3)

if __name__ == "__main__":
    db.create_all()
    app.run(host='127.0.0.1', threaded=True, port=8170, debug=True,)