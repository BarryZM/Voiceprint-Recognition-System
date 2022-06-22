from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()

class Log(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    phone = db.Column(db.String(20))
    time = db.Column(db.DateTime, default=datetime.now)
    action_type = db.Column(db.Integer(),default=0) # test:1 # register:2 # self_test:3 # hit:4
    err_type = db.Column(db.Integer(),default=0)    
    # test:{0:一切正常 1:质量不合格 2:长度不合格  3: 其他错误} register:{0:一切正常 1:质量不合格 2:长度不合格  3: 其他错误}  
    # self_test:{1:TP在黑库中且正确 2:FP1在黑库中但错误(未命中) 3:FP2在黑库中但错误(错误判断其不在黑库中)  4:TN不在黑库中且正确  5:FN 不在黑库中且错误}
    file_url = db.Column(db.String(256),default="")
    message = db.Column(db.String(128))


    # # Action Type
    # test:1
    # register:2
    # self_test:3
    # hit:4

    # # Err Type
    # test:
    #     0:一切正常 1:质量不合格 2:长度不合格  3: 其他错误
    # reigster:
    #     0:一切正常 1:质量不合格 2:长度不合格  3: 其他错误
    # self_test:
    #     1:TP在黑库中且正确 2:FP1在黑库中但错误(未命中) 3:FP2在黑库中但错误(错误判断其不在黑库中)  4:TN不在黑库中且正确  5:FN 不在黑库中且错误
