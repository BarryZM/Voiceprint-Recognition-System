from auto_register.query import Query
from datetime import datetime
import requests
import time
import os
from multiprocessing.dummy import Pool as ThreadPool
# query = Query(-24000)
# print("* 开始自动注册")
# query.now_timestamp = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
# result = query.check_new_record()
# query.pre_timestamp = query.now_timestamp

# print(len(result))

result = []
root = "/mnt/cti_record_data_with_phone_num"
spkid_paths = [os.path.join(root,_file) for _file in os.listdir(root)]
for spkid_path in spkid_paths:
    spkid = spkid_path.split("/")[-1]
    session_paths = [os.path.join(spkid_path,_path) for _path in os.listdir(spkid_path) if "wav" not in _path]
    for session_path in session_paths:
        wav_files = [os.path.join(session_path,_path) for _path in os.listdir(session_path)]
        for wav_file in wav_files:
            if os.path.getsize(wav_file)/(1024*1024)>1:
                result.append(
                    {
                        "record_file_name":"",
                        "caller_num":spkid,
                        "begintime":(datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
                        "endtime":(datetime.now()).strftime("%Y-%m-%d %H:%M:%S"),
                        "wav_url":f"local:{wav_file}"
                    }
                )
print(len(result))




def register(item):
    record_file_name= item["record_file_name"]
    caller_num= item["caller_num"]
    begintime = item["begintime"]
    endtime = item["endtime"]
    if len(caller_num) != 11:
        return
    # wav_url = f"http://116.62.120.233/mpccApi/common/downloadFile.json?type=0&addr={record_file_name}"
    wav_url = item["wav_url"]
    filename = record_file_name.split("/")[-1]
    save_path = f"root/{caller_num}/{filename}"
            
    url="http://127.0.0.1:8180/register/url"
    values = {"spkid": caller_num,"wav_url":wav_url,"call_begintime":begintime,"call_endtime":endtime}
    try:
        resp = requests.request("POST",url=url, data=values)#,headers=headers)
        # print(resp)
        print(resp.json())
        print(f"Registering:\n\t-> URL {url}\n\t-> SPKID {caller_num}\n\t-> Save Path {save_path}")
    except Exception as e:
        print(e)
        return
    print(f"success {caller_num}")

result = result[::-1]
pool = ThreadPool(4)
pool.map(register, result)
pool.close()
pool.join()