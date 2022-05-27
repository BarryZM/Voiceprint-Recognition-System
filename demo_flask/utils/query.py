# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:40:43.000-05:00
# Desc  : query mysql

import pymysql
from datetime import datetime, timedelta

from sympy import re
import json

def check_new_record(pre_timestamp,now_timestamp):
    """query record data in cti_cdr_call

    Returns:
        list: new record
    """
    msg_db = {
        "leave_msg_tb": {
            "host": "116.62.120.233",
            "port": 3306,
            "db": "hostedcti",
            "username": "changjiangsd",
            "passwd": "changjiangsd9987",
            "table": "cticdr"
        },
        "cjcc_server_ip": "116.62.120.233"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "116.62.120.233"),
        port=msg_db.get("port", 3306),
        db=msg_db.get("db", "cticdr"),
        user=msg_db.get("user", "changjiangsd"),
        passwd=msg_db.get("passwd", "changjiangsd9987"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()
    query_sql = f"SELECT cti_record.customer_uuid,\
                    cti_record.begintime,\
                    cti_record.endtime,\
                    cti_record.record_file_name,\
                    cti_cdr_call.caller_num\
                    FROM cti_cdr_call INNER JOIN cti_record \
                    WHERE (cti_cdr_call.call_uuid = cti_record.customer_uuid) \
                    AND (cti_record.timestamp>'{pre_timestamp}') \
                    AND (cti_record.timestamp<'{now_timestamp}') \
                    ORDER BY cti_record.timestamp DESC;"
    cur.execute(query_sql)
    res = cur.fetchall()
    return res

def query_speaker():
    msg_db = {
            "host": "127.0.0.1",
            "port": 3306,
            "db": "si",
            "username": "root",
            "passwd": "123456",
            "table": "speaker"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "127.0.0.1"),
        port=msg_db.get("port", 3306),
        db=msg_db.get("db", "si"),
        user=msg_db.get("user", "root"),
        passwd=msg_db.get("passwd", "123456"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()
    query_sql = f"SELECT *\
                    FROM speaker\
                    ORDER BY register_time DESC;"
    cur.execute(query_sql)
    res = cur.fetchall()

    return_info = []
    
    qset = res
    for index,item in enumerate(qset):
        if index == 10:
            break
        return_info.append({
            "phone":item["phone"],
            "call_begintime":item["call_begintime"].strftime("%Y-%m-%d %H:%M:%S"),
            "call_endtime":item["call_begintime"].strftime("%Y-%m-%d %H:%M:%S"),
            "status":"对比完成"
        })

    numbers = len(qset)

    response = {
        "code": 2000,
        "status": "success",
        "names_10": return_info,
        "numbers": numbers,
        "err_msg": "null",
    }
    return json.dumps(response, ensure_ascii=False)

def query_hit_phone():
    msg_db = {
            "host": "127.0.0.1",
            "port": 3306,
            "db": "si",
            "username": "root",
            "passwd": "123456",
            "table": "speaker"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "127.0.0.1"),
        port=msg_db.get("port", 3306),
        db=msg_db.get("db", "si"),
        user=msg_db.get("user", "root"),
        passwd=msg_db.get("passwd", "123456"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()
    query_sql = "SELECT phone, count(*) as count,any_value(hit_time) as hit_time,any_value(id) as id FROM log WHERE phone IS NOT NULL GROUP BY phone ORDER BY count DESC LIMIT 10;"
    cur.execute(query_sql)
    res = cur.fetchall()
    
    print(res)
    return_dict = {}
    for data in res:
        return_dict[data["phone"]]={
            "phone":data.get("phone",""),
            "id":data.get("id",""),
            "hit_count":data.get("count",""),
            "last_time":data.get("hit_time","").strftime("%Y-%m-%d %H:%M:%S")
        }
    response = {
        "code": 2000,
        "status": "success",
        "hit": return_dict,
    }
    print(response)
    return json.dumps(response, ensure_ascii=False)

def query_hit_location():
    msg_db = {
            "host": "127.0.0.1",
            "port": 3306,
            "db": "si",
            "username": "root",
            "passwd": "123456",
            "table": "speaker"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "127.0.0.1"),
        port=msg_db.get("port", 3306),
        db=msg_db.get("db", "si"),
        user=msg_db.get("user", "root"),
        passwd=msg_db.get("passwd", "123456"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()
    query_sql = "SELECT province, count(*) as count FROM log WHERE province IS NOT NULL GROUP BY province ORDER BY count(*) DESC LIMIT 10;"
    cur.execute(query_sql)
    res = cur.fetchall()
    return_info = []
    for data in res:
        return_info.append([data.get("province",""),data.get("count","")])
    response = {
        "code": 2000,
        "status": "success",
        "hit": return_info,
    }
    return json.dumps(response, ensure_ascii=False)

def query_database_info():
    msg_db = {
            "host": "127.0.0.1",
            "port": 3306,
            "db": "si",
            "username": "root",
            "passwd": "123456",
            "table": "speaker"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "127.0.0.1"),
        port=msg_db.get("port", 3306),
        db=msg_db.get("db", "si"),
        user=msg_db.get("user", "root"),
        passwd=msg_db.get("passwd", "123456"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()
    # query_sql = "SELECT sum(register) as total_register,sum(test) as total_test,sum(hit) as total_hit,sum(self_test) as total_self_test,sum(right) as total_self_test_right FROM info;"
    query_sql = "SELECT sum(test) as total_test,sum(register) as total_register,sum(hit) as total_hit,sum(self_test) as total_self_test,sum(`right`) as total_right FROM info;"
    cur.execute(query_sql)
    res = cur.fetchall()
    print(res)

    total_register = int(res[0].get("total_register",0))
    total_test = int(res[0].get("total_test",0))
    total_hit = int(res[0].get("total_hit",0))
    total_self_test = int(res[0].get("total_self_test",0))
    total_right = int(res[0].get("total_right",0))
    response = {
            "code": 2000,
            "status": "success",
            "err_msg": "null",
            "register":total_register,
            "test":total_test,
            "hit":total_hit,
            "self_test":total_self_test,
            "self_test_right":total_right
        }
    return json.dumps(response, ensure_ascii=False)
    
def query_date_info(date):
    msg_db = {
            "host": "127.0.0.1",
            "port": 3306,
            "db": "si",
            "username": "root",
            "passwd": "123456",
            "table": "speaker"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "127.0.0.1"),
        port=msg_db.get("port", 3306),
        db=msg_db.get("db", "si"),
        user=msg_db.get("user", "root"),
        passwd=msg_db.get("passwd", "123456"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()

    query_sql = f"SELECT * FROM info WHERE date='{date}';"
    cur.execute(query_sql)
    res = cur.fetchall()
    register = res[0].get("register",0)
    test = res[0].get("test",0)
    hit = res[0].get("hit",0)
    self_test = res[0].get("self_test",0)
    right = res[0].get("right",0)
    register_error_1 = res[0].get("register_error_1",0)
    register_error_2 = res[0].get("register_error_2",0)
    register_error_3 = res[0].get("register_error_3",0)
    test_error_1 = res[0].get("test_error_1",0)
    test_error_2 = res[0].get("test_error_2",0)
    test_error_3 = res[0].get("test_error_3",0)

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
    timestamp = (datetime.now() + timedelta(hours=-20)).strftime("%Y-%m-%d %H:%M:%S")
    result = check_new_record(timestamp)
    print(len(result))
    print(result[0]["record_file_name"])
    for item in result:
        record_file_name= item["record_file_name"]
        caller_num= item["caller_num"]
        url = f"http://116.62.120.233/mpccApi/common/downloadFile.json?type=0&addr={record_file_name}"
        begintime = item["begintime"]
        endtime = item["endtime"]
        filename = record_file_name.split("/")[-1]
        save_path = f"root/{caller_num}/{filename}"

        print(f"Registering:\n\t-> URL {url}\n\t-> SPKID {caller_num}\n\t-> Save Path {save_path}")
