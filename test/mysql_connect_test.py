# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:40:43.000-05:00
# Desc  : query mysql

import pymysql
import sys
sys.path.append("/VAF-System/demo_flask")
import cfg

msg_db = cfg.MYSQL

def test():
    """query record data in cti_cdr_call

    Returns:
        list: new record
    """
    
    conn = pymysql.connect(
        host=msg_db.get("host", "116.62.120.233"),
        port=msg_db.get("port", 3306),
        db=msg_db.get("db", "cticdr"),
        user=msg_db.get("username", "changjiangsd"),
        passwd=msg_db.get("passwd", "changjiangsd9987"),
        cursorclass=pymysql.cursors.DictCursor,
    )
    cur = conn.cursor()
    query_sql = f"SELECT * from log;"
    cur.execute(query_sql)
    res = cur.fetchall()
    return res


if __name__ == "__main__":
    result = test()
    print(len(result))
    print(result[0])