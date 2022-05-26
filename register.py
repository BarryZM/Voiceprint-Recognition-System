from auto_register.query import Query
from datetime import datetime
import requests
import time
query = Query(-24000)
print("* 开始自动注册")
query.now_timestamp = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
result = query.check_new_record()
query.pre_timestamp = query.now_timestamp

print(len(result))
for item in result:
    record_file_name= item["record_file_name"]
    caller_num= item["caller_num"]
    begintime = item["begintime"]
    endtime = item["endtime"]
    if len(caller_num) != 11:
        continue
    wav_url = f"http://116.62.120.233/mpccApi/common/downloadFile.json?type=0&addr={record_file_name}"
    filename = record_file_name.split("/")[-1]
    save_path = f"root/{caller_num}/{filename}"
            
    
    url="http://127.0.0.1:8170/register/url"
    values = {"spkid": caller_num,"wav_url":wav_url,"begintime":begintime,"endtime":endtime}
    try:
        resp = requests.request("POST",url=url, data=values)#,headers=headers)
        # print(resp)
        print(resp.json())
        print(f"Registering:\n\t-> URL {url}\n\t-> SPKID {caller_num}\n\t-> Save Path {save_path}")
    except Exception as e:
        print(e)
        time.sleep(10)
        continue

