# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:53:59.000-05:00
# Desc  : utils about database
import pickle
from utils.phone import getPhoneInfo
from datetime import datetime, timedelta
def add_to_database(database,embedding,spkid,wav_file_path,raw_file_path,database_filepath,max_score,mean_score,min_score):
    """add new speaker or new wav to black databse

    Args:
        database (dict): old database
        embedding (torch.tensor): new embedding
        spkid (string): speak id
        wav_file_path (string): wav file path
    """

    # Database Format:{
    #     "embedding_1":编码向量，
    #     "wav":预处理文件路径，
    #     "raw":原始文件路径，
    #     "zip_code":归属地zip_code，
    #     "phone_type":运营商
    #     "time":注册时间
    #     "max_score":自我检验最高分
    #     "mean_socre":自我检验平均分
    #     "min_socre":自我检验最低分
    # }

    if spkid in database.keys():
        return False
    else:
        database[spkid] = {}
    phone_info = getPhoneInfo(spkid)
    database[spkid]["zip_code"] = phone_info['zip_code']
    database[spkid]["phone_type"] = phone_info['phone_type']
    database[spkid]["embedding_1"] = embedding.numpy()
    database[spkid]["wav"] = wav_file_path
    database[spkid]["raw"] = raw_file_path

    database[spkid]["max_score"] = max_score
    database[spkid]["mean_score"] = mean_score
    database[spkid]["min_score"] = min_score

    database[spkid]["time"] = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")

    with open(database_filepath, 'wb') as f:
        pickle.dump(database, f)
    return True