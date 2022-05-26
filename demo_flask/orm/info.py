
class Info(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20))
    adress = db.Column(db.String(60))
    teachers = db.relationship("Teacher", secondary="tracher_class", backref="Class")