import json
import time
from flask import Flask, request, render_template
from flask_cors import CORS
import flask
import torch
import numpy as np
import pickle
import os
from datetime import datetime
from flask_sock import Sock

# utils
from utils.database import add_to_database,get_all_embedding
from utils.save import save_wav_from_url,save_wav_from_file
from utils.preprocess import self_test,vad_and_upsample
from utils.scores import get_scores,self_check
from utils.orm import add_speaker
from utils.phone import getPhoneInfo
from utils.query import query_speaker,query_hit_phone,query_hit_location,query_database_info,query_date_info,check_url_already_exists,add_to_log
from utils.log_wraper import logger,err_logger


# config
import cfg

# encoder
from encoder.encoder import *

# app
app=Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"]=cfg.MYSQL_DATABASE
app.config["SQLALCHEMY_TRACK_MOD/IFICATIONS"]=False
from models.log import db as log_db,Log
from models.speaker import db as speaker_db,Speaker
log_db.app = app
speaker_db.app = app
log_db.init_app(app)
speaker_db.init_app(app)
sock = Sock(app)
CORS(app, supports_credentials=True,
        origins="*", methods="*", allow_headers="*")


# Load blackbase
load_blackbase_start = time.time()
black_database = get_all_embedding(-1)
spks = list(black_database.keys())
spks_num = len(spks)
logger.info(f"** Start! Load database used:{time.time() - load_blackbase_start:.2f}s. Total speaker num:{spks_num}")

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

        logger.info("@ -> Test {new_spkid}")

        
        if test_type == "file":
            new_file = request.files["wav_file"]
            filepath,speech_number = save_wav_from_file(new_file,new_spkid,cfg.TEST_RAW_PATH)
        elif test_type == "url":
            new_url =request.form.get("wav_url")
            filepath,speech_number = save_wav_from_url(new_url,new_spkid,os.path.join(cfg.SAVE_PATH,"raw"))
        start_time = time.time()
        # Preprocess: vad + upsample to 16k + self test
        wav,before_vad_length,after_vad_length,preprocessed_filepath,raw_wav_length,vad_used_time = vad_and_upsample(filepath,savepath=cfg.REGISTER_PREPROCESSED_PATH,spkid=new_spkid,wav_length=cfg.WAV_LENGTH)
        pass_test, msg,self_test_used_time = self_test(wav, spkreg,similarity, sr=16000, split_num=cfg.TEST_SPLIT_NUM, min_length=cfg.MIN_LENGTH, similarity_limit=cfg.SELF_TEST_TH)
        if not pass_test:
            response = {
                "code": 2000,
                "status": "error",
                "err_msg": msg
            }
            if "duration" in msg:
                add_to_log(phone=new_spkid, action_type=1, err_type=2, message=f"{msg}",file_url=new_url)
            else:
                add_to_log(phone=new_spkid, action_type=2, err_type=2, message=f"{msg}",file_url=new_url)
            end_time = time.time()
            time_used = end_time - start_time
            logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
            logger.info(f"\t# Error: {msg}s")
            return json.dumps(response, ensure_ascii=False)


        encode_start_time = time.time()
        embedding = spkreg.encode_batch(wav)[0][0]
        #TODO:预分类模块
        max_class_score = 0
        max_class_index = 0
        for index,i in enumerate(torch.eye(192)):
            now_class_score = similarity(embedding,i)
            if now_class_score>max_class_score:
                max_class_score=now_class_score
                max_class_index = index
    
        black_database = get_all_embedding(max_class_index)
        
        scores,top_list = get_scores(black_database,
                                    embedding,
                                    cfg.BLACK_TH,
                                    similarity,
                                    top_num=10)
        add_to_log(phone=new_spkid, action_type=1, err_type=0, message=f"",file_url=new_url)
        if scores["inbase"] == 1:
            add_to_log(phone=new_spkid, action_type=4, err_type=1, message=f"对比命中：{top_list}",file_url=new_url)
        else:
            add_to_log(phone=new_spkid, action_type=4, err_type=0, message=f"对比未命中：{top_list}",file_url=new_url)

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
        logger.info(f"\t# Wav Length: {raw_wav_length}s")
        logger.info(f"\t# Vad used:{vad_used_time:.2f}s.")
        logger.info(f"\t# Self Test used:{self_test_used_time:.2f}s.")
        logger.info(f"\t# Embed and test used:{time.time() - encode_start_time:.2f}s.")
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
        
        logger.info("# => Register")
        # get request.files
        new_spkid = request.form["spkid"]
        call_begintime = request.form["call_begintime"]
        call_endtime = request.form["call_endtime"]
        
        if register_type == "file":
            new_file = request.files["wav_file"]
            filepath,speech_number = save_wav_from_file(new_file,new_spkid,cfg.REGISTER_RAW_PATH)
            new_url = request.form.get("wav_url")
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
            filepath,speech_number = save_wav_from_url(new_url,new_spkid,cfg.REGISTER_RAW_PATH)
        start_time = time.time()
        # Preprocess: vad + upsample to 16k + self test
        try:
            wav,before_vad_length,after_vad_length,preprocessed_filepath,raw_wav_length,vad_used_time = vad_and_upsample(filepath,savepath=cfg.REGISTER_PREPROCESSED_PATH,spkid=new_spkid,wav_length=cfg.WAV_LENGTH)
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
            add_to_log(phone=new_spkid, action_type=2, err_type=3, message=f"文件读取失败",file_url=new_url)
            return json.dumps(response, ensure_ascii=False)
        
        if cfg.SELF_TEST:
            pass_test, msg,max_score,mean_score,min_score,self_test_used_time = self_test(wav, spkreg,similarity, sr=16000, split_num=cfg.TEST_SPLIT_NUM, min_length=cfg.MIN_LENGTH, similarity_limit=cfg.SELF_TEST_TH)
        else:
            pass_test = True
            msg = ""
            max_score,mean_score,min_score = 999,999,999

        if not pass_test:
            response = {
                "code": 2000,
                "status": "error",
                "err_msg": msg
            }
            if "duration" in msg:
                # 时长不符合要求
                add_to_log(phone=new_spkid, action_type=2, err_type=2, message=f"{msg}",file_url=new_url)
            else:
                # 质量不符合要求
                add_to_log(phone=new_spkid, action_type=2, err_type=1, message=f"{msg}",file_url=new_url)
            end_time = time.time()
            time_used = end_time - start_time
            logger.info(f"\t# Time using: {np.round(time_used, 1)}s")
            logger.info(f"\t# Error: {msg}")
            return json.dumps(response, ensure_ascii=False)

        encode_start_time = time.time()
        embedding = spkreg.encode_batch(wav)[0][0]
        
        #TODO:预分类模块
        max_class_score = 0
        max_class_index = 0
        for index,i in enumerate(torch.eye(192)):
            now_class_score = similarity(embedding,i)
            if now_class_score>max_class_score:
                max_class_score=now_class_score
                max_class_index = index
        



        black_database = get_all_embedding(max_class_index)
        if len(black_database.keys()) > 1:
            if cfg.AUTO_TESTING_MODE:
                predict_right,status,pre_test_msg = self_check(database=black_database,
                                            embedding=embedding,
                                            spkid=new_spkid,
                                            black_limit=cfg.BLACK_TH,
                                            similarity=similarity,
                                            top_num=10)               
                add_to_log(phone=new_spkid, action_type=3, err_type=status, message=f"{pre_test_msg}",file_url=new_url)
                if predict_right:
                    
                    logger.info(f"\t# Pre-test pass √")
                    logger.info(f"\t# Pre-test msg:{pre_test_msg}")
                    
                    # if cfg.LOG_PHONE_INFO:
                    #     phone_info = getPhoneInfo(new_spkid)
                    #     if phone_info == None:
                    #         phone_info = {}

                else:
                    logger.info(f"\t# Pre-test error !")
                    logger.info(f"\t# Pre-test msg:{pre_test_msg}")
                    # TODO 将error添加到mysql做记录
        
        logger.info(f"\t# Wav Length: {raw_wav_length}s")
        logger.info(f"\t# Vad used:{vad_used_time:.2f}s.")
        logger.info(f"\t# Self Test used:{self_test_used_time:.2f}s.")
        logger.info(f"\t# Embed and test used:{time.time() - encode_start_time:.2f}s.")


        add_success,phone_info = add_to_database(
                                        embedding=embedding,
                                        spkid=new_spkid,
                                        max_class_index=max_class_index,
                                        log_phone_info = cfg.LOG_PHONE_INFO
                                        )
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
        add_speaker(skp_info,speaker_db,Speaker)
        print("register info add to msyql")
        add_to_log(phone=new_spkid, action_type=2, err_type=0, message=f"{msg}",file_url=new_url)
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
    log_db.create_all()
    speaker_db.create_all()
    app.run(host='0.0.0.0', threaded=True, port=8180, debug=True,)