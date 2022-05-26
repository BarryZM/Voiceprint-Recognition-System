from django.db import models
import datetime
# Create your models here.
class VoicePrint(models.Model):
    speaker = models.CharField('说话人姓名',max_length=256)
    phone_number = models.CharField('手机号',max_length=256)
    zip_code = models.CharField('邮政编码')
    province = models.CharField('省份')
    city = models.CharField('城市')
    phone_type = models.CharField('运营商')
    zip_code = models.CharField('邮政编码')
    check_number = models.IntegerField('比对次数')
    hit_number = models.IntegerField('命中次数')
    register_time = models.DateTimeField('注册时间',default = datetime.datetime.now())
    change_time = models.DateTimeField('修改时间',default = datetime.datetime.now())
    self_test_score_mean = models.FloatField('自我检测平均分')
    self_test_score_max = models.FloatField('自我检测最高分')
    self_test_score_min = models.FloatField('自我检测最低分')

class CompareLog(models.Model):
    speaker = models.CharField('说话人姓名',max_length=256)
    phone_number = models.CharField('手机号',max_length=256)
    hit = models.IntegerField('是否命中')
    result_1 = models.CharField('top1')
    result_2 = models.CharField('top2')
    result_3 = models.CharField('top3')
    result_4 = models.CharField('top4')
    result_5 = models.CharField('top5')

