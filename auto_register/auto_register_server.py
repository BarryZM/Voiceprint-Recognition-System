# importing flask module
from flask import Flask
from flask_apscheduler import APScheduler
from datetime import datetime, timedelta
from query import Query
from flask import Flask
from datetime import datetime
from flask_apscheduler import APScheduler
import requests
aps = APScheduler()

# initializing a variable of Flask
app = Flask(__name__)
query = Query()

class Config(object):
    JOBS = [
        {
            'id': 'job1',
            'func': 'auto_register_server:task',
            'args': (1, 2),
            'trigger': 'interval',
            'seconds': 10
        }
    ]
    SCHEDULER_API_ENABLED = True


def task(a, b):
    print("* 开始自动注册")
    query.now_timestamp = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    result = query.check_new_record()
    query.pre_timestamp = query.now_timestamp
    
    print(len(result))
    for item in result:
        record_file_name= item["record_file_name"]
        caller_num= item["caller_num"]
        wav_url = f"http://116.62.120.233/mpccApi/common/downloadFile.json?type=0&addr={record_file_name}"
        filename = record_file_name.split("/")[-1]
        save_path = f"root/{caller_num}/{filename}"
                
        
        url="http://127.0.0.1:8170/register/url"
        values = {"spkid": caller_num,"wav_url":wav_url}
        resp = requests.request("POST",url=url, data=values)#,headers=headers)
        # print(resp)
        print(resp.json())
        print(f"Registering:\n\t-> URL {url}\n\t-> SPKID {caller_num}\n\t-> Save Path {save_path}")


# decorating index function with the app.route
@app.route('/')
def index():
   return "WELCOME!!! This is the home page"
 
if __name__ == "__main__":

    app = Flask(__name__)
    app.config.from_object(Config())

    scheduler = APScheduler()
    scheduler.init_app(app)
    scheduler.start()

    app.run(port=8190)
    # app.config.from_object(Config())
    # scheduler = APScheduler()
    # scheduler.init_app(app)
    # scheduler.start()
    # # sockets = Sockets(app)
    # app.run(host='127.0.0.1', threaded=True, port=8190, debug=True,)