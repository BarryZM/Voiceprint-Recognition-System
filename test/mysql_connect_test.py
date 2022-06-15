# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:40:43.000-05:00
# Desc  : query mysql

import pymysql
from datetime import datetime, timedelta

from sympy import re


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


if __name__ == "__main__":
    pre_timestamp = (datetime.now() + timedelta(minutes=-5)).strftime("%Y-%m-%d %H:%M:%S")
    now_timestamp = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    result = check_new_record(pre_timestamp,now_timestamp)
    print(len(result))
    print(result[0])
    # for item in result:
    #     record_file_name= item["record_file_name"]
    #     caller_num= item["caller_num"]
    #     url = f"http://116.62.120.233/mpccApi/common/downloadFile.json?type=0&addr={record_file_name}"
    #     filename = record_file_name.split("/")[-1]
    #     save_path = f"root/{caller_num}/{filename}"

    #     print(f"Registering:\n\t-> URL {url}\n\t-> SPKID {caller_num}\n\t-> Save Path {save_path}")
