# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:40:43.000-05:00
# Desc  : query mysql

import pymysql
from datetime import datetime, timedelta
import json


def check_new_record(pre_timestamp,now_timestamp):
    """query record data in cti_cdr_call

    Returns:
        list: new record
    """
    msg_db = {
        "leave_msg_tb": {
            "host": "116.62.120.233",
            "port": 27546,
            "db": "hostedcti",
            "username": "changjiangsd",
            "passwd": "changjiangsd9987",
            "table": "cticdr"
        },
        "cjcc_server_ip": "116.62.120.233"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "116.62.120.233"),
        port=msg_db.get("port", 27546),
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
                    AND (cti_cdr_call.call_lasts_time>60) \
                    AND (cti_record.record_status=2) \
                    ORDER BY cti_record.timestamp DESC;"
    cur.execute(query_sql)
    res = cur.fetchall()
    return res

def query_speaker():
    msg_db = {
            "host": "zhaosheng.mysql.rds.aliyuncs.com",
            "port": 27546,
            "db": "si",
            "username": "root",
            "passwd": "Nt3380518!zhaosheng123",
            "table": "speaker"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "zhaosheng.mysql.rds.aliyuncs.com"),
        port=msg_db.get("port", 27546),
        db=msg_db.get("db", "si"),
        user=msg_db.get("user", "root"),
        passwd=msg_db.get("passwd", "Nt3380518!zhaosheng123"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()
    query_sql = f"SELECT *\
                    FROM speaker \
                    WHERE status=1 \
                    ORDER BY call_endtime DESC;"
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
            "call_endtime":item["call_endtime"].strftime("%Y-%m-%d %H:%M:%S"),
            "span_time":str(item["call_endtime"]-item["call_begintime"]),
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
            "host": "zhaosheng.mysql.rds.aliyuncs.com",
            "port": 27546,
            "db": "si",
            "username": "root",
            "passwd": "Nt3380518!zhaosheng123",
            "table": "speaker"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "zhaosheng.mysql.rds.aliyuncs.com"),
        port=msg_db.get("port", 27546),
        db=msg_db.get("db", "si"),
        user=msg_db.get("user", "root"),
        passwd=msg_db.get("passwd", "Nt3380518!zhaosheng123"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()
    # query_sql = "SELECT phone, count(*) as count,any_value(hit_time) as hit_time,any_value(id) as id FROM log WHERE phone IS NOT NULL GROUP BY phone ORDER BY count DESC LIMIT 10;"
    query_sql = "SELECT log.phone, count(*) as count,any_value(log.time) as hit_time,any_value(speaker.id) as id \
                FROM log INNER JOIN speaker ON log.phone=table speaker.phone \
                WHERE (log.action_type=4) AND log.phone IS NOT NULL GROUP BY log.phone ORDER BY count DESC LIMIT 10;"
    cur.execute(query_sql)
    res = cur.fetchall()
    

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

    return json.dumps(response, ensure_ascii=False)

def query_hit_location():
    msg_db = {
            "host": "zhaosheng.mysql.rds.aliyuncs.com",
            "port": 27546,
            "db": "si",
            "username": "root",
            "passwd": "Nt3380518!zhaosheng123",
            "table": "speaker"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "zhaosheng.mysql.rds.aliyuncs.com"),
        port=msg_db.get("port", 27546),
        db=msg_db.get("db", "si"),
        user=msg_db.get("user", "root"),
        passwd=msg_db.get("passwd", "Nt3380518!zhaosheng123"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()
    # query_sql = "SELECT province, count(*) as count FROM log WHERE province IS NOT NULL GROUP BY province ORDER BY count(*) DESC LIMIT 10;"

    query_sql = "SELECT speaker.province, count(*) as count\
                FROM log INNER JOIN speaker ON log.phone=table speaker.phone \
                WHERE (log.action_type=4) AND log.phone IS NOT NULL \
                GROUP BY speaker.province \
                ORDER BY count DESC LIMIT 10;"
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
            "host": "zhaosheng.mysql.rds.aliyuncs.com",
            "port": 27546,
            "db": "si",
            "username": "root",
            "passwd": "Nt3380518!zhaosheng123",
            "table": "speaker"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "zhaosheng.mysql.rds.aliyuncs.com"),
        port=msg_db.get("port", 27546),
        db=msg_db.get("db", "si"),
        user=msg_db.get("user", "root"),
        passwd=msg_db.get("passwd", "Nt3380518!zhaosheng123"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()
    # query_sql = "SELECT sum(register) as total_register,sum(test) as total_test,sum(hit) as total_hit,sum(self_test) as total_self_test,sum(right) as total_self_test_right FROM info;"
    # query_sql = "SELECT sum(test) as total_test,sum(register) as total_register,sum(hit) as total_hit,sum(self_test) as total_self_test,sum(`right`) as total_right FROM info;"
    
    # Test
    query_sql = "SELECT count(*) as total_test FROM log \
                    WHERE action_type=1 AND err_type=0;"
    cur.execute(query_sql)
    res = cur.fetchall()
    total_test = int(res[0].get("total_test",0))
    
    # Register
    query_sql = "SELECT count(*) as total_register FROM log \
                    WHERE action_type=2 AND err_type=0;"
    cur.execute(query_sql)
    res = cur.fetchall()
    total_register = int(res[0].get("total_register",0))

    # Hit
    query_sql = "SELECT count(*) as total_hit FROM log \
                    WHERE action_type=4 AND err_type=0;"
    cur.execute(query_sql)
    res = cur.fetchall()
    total_hit = int(res[0].get("total_hit",0))

    # self_test
    query_sql = "SELECT count(*) as total_self_test FROM log \
                    WHERE action_type=3;"
    cur.execute(query_sql)
    res = cur.fetchall()
    total_self_test = int(res[0].get("total_self_test",0))

    # self_test_right
    query_sql = "SELECT count(*) as total_self_test_right FROM log \
                    WHERE action_type=3 AND err_type=0;"
    cur.execute(query_sql)
    res = cur.fetchall()
    total_right = int(res[0].get("total_self_test_right",0))

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
            "host": "zhaosheng.mysql.rds.aliyuncs.com",
            "port": 27546,
            "db": "si",
            "username": "root",
            "passwd": "Nt3380518!zhaosheng123",
            "table": "speaker"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "zhaosheng.mysql.rds.aliyuncs.com"),
        port=msg_db.get("port", 27546),
        db=msg_db.get("db", "si"),
        user=msg_db.get("user", "root"),
        passwd=msg_db.get("passwd", "Nt3380518!zhaosheng123"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()

    # query_sql = f"SELECT * FROM info WHERE date='{date}';"
    
    # Test
    query_sql = "SELECT count(*) as total_test FROM log \
                    WHERE action_type=1 AND err_type=0 AND date='{date};"
    cur.execute(query_sql)
    res = cur.fetchall()
    test = int(res[0].get("total_test",0))
    
    # Register
    query_sql = "SELECT count(*) as total_register FROM log \
                    WHERE action_type=2 AND err_type=0 AND date='{date};"
    cur.execute(query_sql)
    res = cur.fetchall()
    register = int(res[0].get("total_register",0))

    # Hit
    query_sql = "SELECT count(*) as total_hit FROM log \
                    WHERE action_type=4 AND err_type=0 AND date='{date};"
    cur.execute(query_sql)
    res = cur.fetchall()
    hit = int(res[0].get("total_hit",0))

    # self_test
    query_sql = "SELECT count(*) as total_self_test FROM log \
                    WHERE action_type=3 AND date='{date};"
    cur.execute(query_sql)
    res = cur.fetchall()
    self_test = int(res[0].get("total_self_test",0))

    # self_test_right
    query_sql = "SELECT count(*) as total_self_test_right FROM log WHERE action_type=3 AND err_type=0 AND date='{date};"
    cur.execute(query_sql)
    res = cur.fetchall()
    right = int(res[0].get("total_self_test_right",0))


    # cur.execute(query_sql)
    # res = cur.fetchall()
    if len(res)==0:
        response = {
            "code": 2000,
            "status": "success",
            "err_msg": "null",
            "register":0,
            "test":0,
            "hit":0,
            "self_test":1,
            "right":1,
            "register_error_1":0,
            "register_error_2":0,
            "register_error_3":0,
            "test_error_1":0,
            "test_error_2":0,
            "test_error_3":0,
        }
        return json.dumps(response, ensure_ascii=False)
    # register = res[0].get("register",0)
    # test = res[0].get("test",0)
    # hit = res[0].get("hit",0)
    # self_test = res[0].get("self_test",0)
    # right = res[0].get("right",0)
    # register_error_1 = res[0].get("register_error_1",0)
    # register_error_2 = res[0].get("register_error_2",0)
    # register_error_3 = res[0].get("register_error_3",0)
    # test_error_1 = res[0].get("test_error_1",0)
    # test_error_2 = res[0].get("test_error_2",0)
    # test_error_3 = res[0].get("test_error_3",0)

    response = {
            "code": 2000,
            "status": "success",
            "err_msg": "null",
            "register":register,
            "test":test,
            "hit":hit,
            "self_test":self_test,
            "right":right,
            # "register_error_1":register_error_1,
            # "register_error_2":register_error_2,
            # "register_error_3":register_error_3,
            # "test_error_1":test_error_1,
            # "test_error_2":test_error_2,
            # "test_error_3":test_error_3,
        }
    return json.dumps(response, ensure_ascii=False)
    
def check_url_already_exists(url):
    msg_db = {
            "host": "zhaosheng.mysql.rds.aliyuncs.com",
            "port": 27546,
            "db": "si",
            "username": "root",
            "passwd": "Nt3380518!zhaosheng123",
            "table": "speaker"
    }



    

    while True:
        try:
            conn = pymysql.connect(
                host=msg_db.get("host", "zhaosheng.mysql.rds.aliyuncs.com"),
                port=msg_db.get("port", 27546),
                db=msg_db.get("db", "si"),
                user=msg_db.get("user", "root"),
                passwd=msg_db.get("passwd", "Nt3380518!zhaosheng123"),
                cursorclass=pymysql.cursors.DictCursor,
            )
            cur = conn.cursor()
            query_sql = f"SELECT * FROM log WHERE file_url='{url}';"
            cur.execute(query_sql)
            res = cur.fetchall()
            if len(res) != 0:
                return True
            else:
                return False
        except Exception as error:
            conn.ping(True)

def add_to_log(phone, action_type, err_type, message,file_url):
    msg_db = {
            "host": "zhaosheng.mysql.rds.aliyuncs.com",
            "port": 27546,
            "db": "si",
            "username": "root",
            "passwd": "Nt3380518!zhaosheng123",
            "table": "speaker"
    }

    conn = pymysql.connect(
        host=msg_db.get("host", "zhaosheng.mysql.rds.aliyuncs.com"),
        port=msg_db.get("port", 27546),
        db=msg_db.get("db", "si"),
        user=msg_db.get("user", "root"),
        passwd=msg_db.get("passwd", "Nt3380518!zhaosheng123"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()

    query_sql = f"INSERT INTO log (phone, action_type,time,err_type, message,file_url) VALUES ('{phone}', '{action_type}', curtime(),'{err_type}', '{message}','{file_url}');"
    cur.execute(query_sql)
    conn.commit()
    print(query_sql)

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
