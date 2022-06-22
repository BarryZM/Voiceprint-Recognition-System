# importing flask module

from flask import Flask
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta
from query import Query
from flask import Flask
from datetime import datetime
from flask_apscheduler import APScheduler
import requests
from time import time
from multiprocessing.dummy import Pool as ThreadPool

from logging.handlers import RotatingFileHandler
import logging
import time
#计算时间函数  
# def log_run_time(func):  
#     def wrapper(*args, **kw):  
#         local_time = time.time()  
#         func(*args, **kw) 
#         logger.info(f"\t * {func.__name__} used {time.time() - local_time}")
#     return wrapper

# log
logger = logging.getLogger("auto_register")
logger.setLevel(logging.DEBUG)
formatter = logging.Formatter(
    "[%(asctime)s]  %(levelname)s  [%(filename)s]  #%(lineno)d <%(process)d:%(thread)d>  %(message)s",
    datefmt="[%Y-%m-%d %H:%M:%S]",
)
handler = RotatingFileHandler(
    "./log/auto_register.log", maxBytes=20 * 1024 * 1024, backupCount=5, encoding="utf-8"
)
handler.setFormatter(formatter)
handler.namer = lambda x: "auto_register." + x.split(".")[-1]
logger.addHandler(handler)

aps = APScheduler()
POOL_NUM = 4
url="http://192.168.12.68:8180/register/url"

# initializing a variable of Flask
app = Flask(__name__)
query = Query(-1)

class Config(object):
    JOBS = [
        {
            'id': 'job1',
            'func': 'auto_register_server:task',
            'trigger': 'interval',
            'seconds': 120
        }
    ]
    SCHEDULER_API_ENABLED = True




def reigster_item(item):
    logger.info(item)
    record_file_name= item["record_file_name"]
    caller_num= item["caller_num"]
    begintime = item["begintime"]
    endtime = item["endtime"]
    if len(caller_num) != 11:
        return False
    wav_url = f"http://116.62.120.233/mpccApi/common/downloadFile.json?type=0&addr={record_file_name}"
    filename = record_file_name.split("/")[-1]
    save_path = f"root/{caller_num}/{filename}"
    values = {"spkid": caller_num,"wav_url":wav_url,"call_begintime":begintime,"call_endtime":endtime}
    logger.info(values)
    try:
        resp = requests.request("POST",url=url, data=values)#,headers=headers)
        # print(resp)
        print(resp.json())
        print(f"Registering:\n\t-> URL {url}\n\t-> SPKID {caller_num}\n\t-> Save Path {save_path}")
    except Exception as e:
        print(e)
        return False
    return True

def task():
    now = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    query.now_timestamp = now
    logger.info(f"* {now} 开始自动注册")

    result = query.check_new_record()
    query.pre_timestamp = query.now_timestamp
    logger.info(f"\t找到新通话记录: {len(result)} 条。")
   
    pool = ThreadPool(POOL_NUM)
    pool.map(reigster_item, result)
    pool.close()
    pool.join()
        
app = Flask(__name__)
app.config.from_object(Config())
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()
if __name__ == "__main__":
    
    app.run(port=8190,threaded=False, debug=False,)