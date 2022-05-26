from email.policy import default
from hashlib import new
from logging.handlers import RotatingFileHandler
import json
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
app.config["SQLALCHEMY_DATABASE_URI"]="mysql://root:123456@127.0.0.1:3306/si"
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
    name = db.Column(db.String(20),default="none")
    uuid = db.Column(db.String(256))
    phone = db.Column(db.String(256))
    hit = db.Column(db.Integer,default=0)
    register_time = db.Column(db.DateTime, default=datetime.now)
    province = db.Column(db.String(20))
    city = db.Column(db.String(20))
    phone_type = db.Column(db.String(20))
    area_code = db.Column(db.String(20))
    zip_code = db.Column(db.String(20))
    self_test_score_mean = db.Column(db.Float(),default=0.0)
    self_test_score_min = db.Column(db.Float(),default=0.0)
    self_test_score_max = db.Column(db.Float(),default=0.0)
    call_begintime = db.Column(db.DateTime, default=datetime.now)
    call_endtime = db.Column(db.DateTime, default=datetime.now)

class Log(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    hit_time = db.Column(db.DateTime, default=datetime.now)
    phone = db.Column(db.String(256))
    province = db.Column(db.String(20))
    city = db.Column(db.String(20))
    phone_type = db.Column(db.String(20))


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
@app.route('/info', methods=["GET"])
def getInfo():
    
    if request.method == "GET":
        time.sleep(3)
        names_10 = list(black_database.keys())[-10:]
        number = len(black_database.keys())
        response = {
            "code": 2000,
            "status": "success",
            "register_number_total": number,
            "register_number_today":today_regitster,
            "test_number_today":today_test,
            "hits_number_today":today_hits_number,
            "hits_number_total":total_hits_number,
            "todal_self_test":today_self_test,
            "today_right":today_right,
            "names_10":names_10,
            "err_msg": "null"
        }
        return json.dumps(response, ensure_ascii=False)

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
            if "duration" in msg:
                add_error("test",2,db,Info)
            else:
                add_error("test",1,db,Info)
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
        add_test(db,Info)
        if scores["inbase"] == 1:
            add_hit(db,Info)
            phone_info = getPhoneInfo(new_spkid)
            log_info ={
                "city":phone_info.get("city",None),
                "province":phone_info.get("province",None),
                "phone_type":phone_info.get("phone_type",None),
                "hit_time":datetime.now(),
                "phone":new_spkid
            }
            add_log(log_info,db,Log)
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

# 最近注册信息
@app.route("/namelist", methods=["GET"])
def namelist():
    if request.method == "GET":
        # TODO: 返回前十个人的手机号，状态，通话开始时间，通话时长
        return_info = []
        qset = Speaker.query.order_by(desc(Speaker.register_time)).all()
        for index,item in enumerate(qset):
            if index == 10:
                break
            return_info.append({
                "phone":item.phone,
                "call_begintime":item.call_begintime.strftime("%Y-%m-%d %H:%M:%S"),
                "call_endtime":item.call_begintime.strftime("%Y-%m-%d %H:%M:%S")
            })

        numbers = len(qset)

        response = {
            "code": 2000,
            "status": "success",
            "names_10": return_info,
            "numbers": numbers,
            "err_msg": "null",
        }
        print(response)
        return json.dumps(response, ensure_ascii=False)


@sock.route('/namelist_ws')
def namelist_ws(sock):
    while True:
        data = sock.receive()
        print(data)
        while True:
            time.sleep(3)
            return_info = []
            qset = Speaker.query.order_by(desc(Speaker.register_time)).all()
            for index,item in enumerate(qset):
                if index == 10:
                    break
                return_info.append({
                    "phone":item.phone,
                    "call_begintime":item.call_begintime.strftime("%Y-%m-%d %H:%M:%S"),
                    "call_endtime":item.call_begintime.strftime("%Y-%m-%d %H:%M:%S")
                })

            numbers = len(qset)

            response = {
                "code": 2000,
                "status": "success",
                "names_10": return_info,
                "numbers": numbers,
                "err_msg": "null",
            }
            print(response)
            # return json.dumps(response, ensure_ascii=False)
            sock.send(json.dumps(response, ensure_ascii=False))


# 比中信息
@app.route("/hit_info", methods=["GET"])
def hit_info():
    if request.method == "GET":
        # TODO: 返回各个省份的比重数量
        return_info = []

        query = db.session.query(Log.province.distinct().label("province"))
        provinces = [row.province for row in query.all()]
        # print(provinces)
        for province in provinces:
            number = len(Log.query.filter_by(province=province).all())
            return_info.append([province,number])
       
        response = {
            "code": 2000,
            "status": "success",
            "hit": return_info,
        }
        print(response)
        return json.dumps(response, ensure_ascii=False)


@sock.route('/hit_info_ws')
def hit_info_ws(sock):
    while True:
        data = sock.receive()
        print(data)
        while True:
            time.sleep(3)
            return_info = []

            query = db.session.query(Log.province.distinct().label("province"))
            provinces = [row.province for row in query.all()]
            # print(provinces)
            for province in provinces:
                number = len(Log.query.filter_by(province=province).all())
                return_info.append([province,number])
        
            response = {
                "code": 2000,
                "status": "success",
                "hit": return_info,
            }
            print(response)
            # return json.dumps(response, ensure_ascii=False)
            sock.send(json.dumps(response, ensure_ascii=False))


# 声纹注册模块
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
        begintime = request.form.get("begintime")
        endtime = request.form.get("endtime")
        
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
            logger.info(f"\t# Error: 文件读取失败")
            add_error("register",3,db,Info)
            return json.dumps(response, ensure_ascii=False)

        pass_test, msg,max_score,mean_score,min_score = self_test(wav, spkreg,similarity, sr=16000, split_num=cfg.TEST_SPLIT_NUM, min_length=cfg.MIN_LENGTH, similarity_limit=cfg.SELF_TEST_TH)
        
        if not pass_test:
            response = {
                "code": 2000,
                "status": "error",
                "err_msg": msg
            }
            if "duration" in msg:
                add_error("register",2,db,Info)
            else:
                add_error("register",1,db,Info)
            end_time = time.time()
            time_used = end_time - start_time
            logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
            logger.info(f"\t# Error: {msg}")
            return json.dumps(response, ensure_ascii=False)

        embedding = spkreg.encode_batch(wav)[0][0]
        
        if len(black_database.keys()) > 1:
            if cfg.AUTO_TESTING_MODE:
                predict_right,pre_test_msg = self_check(database=black_database,
                                            embedding=embedding,
                                            spkid=new_spkid,
                                            black_limit=cfg.BLACK_TH,
                                            similarity=similarity,
                                            top_num=10)               
                add_self_test(db,Info)
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
                    add_log(log_info,db,Log)
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
            logger.info(f"\t# Error: Already in database! Skipped!")
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
        add_register(db,Info)
        skp_info = {
            "name":"none",
            "phone":new_spkid,
            "uuid":new_url,
            "hit":0,
            "register_time":datetime.now(),
            "province":phone_info["province"],
            "city":phone_info["city"],
            "phone_type":phone_info["phone_type"],
            "area_code":phone_info["area_code"],
            "zip_code":phone_info["zip_code"],
            "self_test_score_mean":mean_score.numpy(),
            "self_test_score_min":min_score.numpy(),
            "self_test_score_max":max_score.numpy(),
            "call_begintime":begintime,
            "call_endtime":endtime
        }
        add_speaker(skp_info,db,Speaker)
        print("register info add to msyql")
        return json.dumps(response, ensure_ascii=False)

# Websocket实时更新注册人数等信息   
@sock.route('/database_info_ws')
def database_info_ws(sock):
    while True:
        data = sock.receive()
        print(data)
        while True:
            time.sleep(3)
            total_register = int(Info.query.with_entities(func.sum(Info.register).label('total')).first().total)
            total_test = int(Info.query.with_entities(func.sum(Info.test).label('total')).first().total)
            total_hit = int(Info.query.with_entities(func.sum(Info.hit).label('total')).first().total)
            total_self_test = int(Info.query.with_entities(func.sum(Info.self_test).label('total')).first().total)
            total_self_test_right = int(Info.query.with_entities(func.sum(Info.right).label('total')).first().total)
            response = {
                    "code": 2000,
                    "status": "success",
                    "err_msg": "null",
                    "register":total_register,
                    "test":total_test,
                    "hit":total_hit,
                    "self_test":total_self_test,
                    "self_test_right":total_self_test_right
                }
            # return json.dumps(response, ensure_ascii=False)
            sock.send(json.dumps(response, ensure_ascii=False))

# 声纹数据库总体信息
@app.route("/database_info",methods=["GET"])
def database_info():
    total_register = int(Info.query.with_entities(func.sum(Info.register).label('total')).first().total)
    total_test = int(Info.query.with_entities(func.sum(Info.test).label('total')).first().total)
    total_hit = int(Info.query.with_entities(func.sum(Info.hit).label('total')).first().total)
    total_self_test = int(Info.query.with_entities(func.sum(Info.self_test).label('total')).first().total)
    total_self_test_right = int(Info.query.with_entities(func.sum(Info.right).label('total')).first().total)
    response = {
            "code": 2000,
            "status": "success",
            "err_msg": "null",
            "register":total_register,
            "test":total_test,
            "hit":total_hit,
            "self_test":total_self_test,
            "self_test_right":total_self_test_right
        }
    return json.dumps(response, ensure_ascii=False)

@sock.route('/date_info_ws')
def date_info_ws(sock):
    while True:
        data = sock.receive()
        print(data)
        while True:
            time.sleep(3)
            date = time.strftime("%Y%m%d",time.localtime(time.time()))
            register = int(Info.query.filter_by(date=date).first().register)
            test     = int(Info.query.filter_by(date=date).first().test)
            hit      = int(Info.query.filter_by(date=date).first().hit)
            self_test= int(Info.query.filter_by(date=date).first().self_test)
            right    = int(Info.query.filter_by(date=date).first().right)
            register_error_1 = int(Info.query.filter_by(date=date).first().register_error_1)
            register_error_2 = int(Info.query.filter_by(date=date).first().register_error_2)
            register_error_3 = int(Info.query.filter_by(date=date).first().register_error_3)
            test_error_1 = int(Info.query.filter_by(date=date).first().test_error_1)
            test_error_2 = int(Info.query.filter_by(date=date).first().test_error_2)
            test_error_3 = int(Info.query.filter_by(date=date).first().test_error_3)
            response = {
                    "code": 2000,
                    "status": "success",
                    "err_msg": "null",
                    "register":register,
                    "test":test,
                    "hit":hit,
                    "self_test":self_test,
                    "right":right,
                    "register_error_1":register_error_1,
                    "register_error_2":register_error_2,
                    "register_error_3":register_error_3,
                    "test_error_1":test_error_1,
                    "test_error_2":test_error_2,
                    "test_error_3":test_error_3,
                }
            # return json.dumps(response, ensure_ascii=False)
            sock.send(json.dumps(response, ensure_ascii=False))

# 每日概况信息
@app.route("/date_info", methods=["POST"])
def date_info():
    date = flask.request.form.get("date")
    register = int(Info.query.filter_by(date=date).first().register)
    test     = int(Info.query.filter_by(date=date).first().test)
    hit      = int(Info.query.filter_by(date=date).first().hit)
    self_test= int(Info.query.filter_by(date=date).first().self_test)
    right    = int(Info.query.filter_by(date=date).first().right)
    register_error_1 = int(Info.query.filter_by(date=date).first().register_error_1)
    register_error_2 = int(Info.query.filter_by(date=date).first().register_error_2)
    register_error_3 = int(Info.query.filter_by(date=date).first().register_error_3)
    test_error_1 = int(Info.query.filter_by(date=date).first().test_error_1)
    test_error_2 = int(Info.query.filter_by(date=date).first().test_error_2)
    test_error_3 = int(Info.query.filter_by(date=date).first().test_error_3)
    response = {
            "code": 2000,
            "status": "success",
            "err_msg": "null",
            "register":register,
            "test":test,
            "hit":hit,
            "self_test":self_test,
            "right":right,
            "register_error_1":register_error_1,
            "register_error_2":register_error_2,
            "register_error_3":register_error_3,
            "test_error_1":test_error_1,
            "test_error_2":test_error_2,
            "test_error_3":test_error_3,
        }
    return json.dumps(response, ensure_ascii=False)


if __name__ == "__main__":
    db.create_all()
    app.run(host='127.0.0.1', threaded=True, port=8170, debug=True,)