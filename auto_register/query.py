from datetime import datetime, timedelta
import pymysql
class Query(object):
    def __init__(self):
        self.pre_timestamp=(datetime.now() + timedelta(hours=-30)).strftime("%Y-%m-%d %H:%M:%S")
        self.now_timestamp=(datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    
    def check_new_record(self):
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
                        AND (cti_record.timestamp>'{self.pre_timestamp}') \
                        AND (cti_record.timestamp<'{self.now_timestamp}') \
                        ORDER BY cti_record.timestamp DESC;"
        cur.execute(query_sql)
        res = cur.fetchall()
        return res