from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

class Speaker(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(10),default="none")
    file_url = db.Column(db.String(256))
    phone = db.Column(db.String(12))
    register_time = db.Column(db.DateTime, default=datetime.now)
    province = db.Column(db.String(10))
    city = db.Column(db.String(10))
    phone_type = db.Column(db.String(10))
    area_code = db.Column(db.String(10))
    zip_code = db.Column(db.String(10))
    self_test_score_mean = db.Column(db.Float(8),default=0.0)
    self_test_score_min = db.Column(db.Float(8),default=0.0)
    self_test_score_max = db.Column(db.Float(8),default=0.0)
    call_begintime = db.Column(db.DateTime)
    call_endtime = db.Column(db.DateTime)
    status = db.Column(db.Integer(),default=1)                          # 0.未激活  1.激活
    class_number = db.Column(db.Integer())                    # 声纹预分类的类别
    hit_count = db.Column(db.Integer(),default=0)