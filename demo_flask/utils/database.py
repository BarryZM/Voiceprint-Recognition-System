# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:53:59.000-05:00
# Desc  : utils about database
import pickle
from utils.phone import getPhoneInfo
from datetime import datetime, timedelta
# import torch
# similarity = torch.nn.CosineSimilarity(dim=-1, eps=1e-6)
import struct
import redis
import numpy as np

# Redis connection
r = redis.Redis(host='localhost', port=6379, db=0)


def toRedis(r,a,n):
   """Store given Numpy array 'a' in Redis under key 'n'"""

   shape = struct.pack('>II',192,1)
   encoded = shape + a.tobytes()

   # Store encoded data in Redis
   r.set(n,encoded)
   return

def fromRedis(r,n):
   """Retrieve Numpy array from Redis key 'n'"""
   encoded = r.get(n)
   h, w = struct.unpack('>II',encoded[:8])
   # Add slicing here, or else the array would differ from the original
   a = np.frombuffer(encoded[8:]).reshape(h,w)
   return a

# # Create 80x80 numpy array to store
# a0 = np.arange(6400,dtype=np.uint16).reshape(80,80) 


# # Store array a0 in Redis under name 'a0array'
# toRedis(r,a0,'a0array')

# # Retrieve from Redis
# a1 = fromRedis(r,'a0array')

# np.testing.assert_array_equal(a0,a1)


def add_to_database(database,embedding,spkid,wav_file_path,raw_file_path,database_filepath,max_score,mean_score,min_score,max_class_index):
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
    #     "max_clas_index":分类
    # }

    # TODO: 添加预分类
    phone_info = getPhoneInfo(spkid)
    if spkid in database.keys():
        return False,phone_info
    else:
        database[spkid] = {}
        
    
    if phone_info:
        database[spkid]["zip_code"] = phone_info['zip_code']
        database[spkid]["phone_type"] = phone_info['phone_type']
    else:
        database[spkid]["zip_code"] = "None"
        database[spkid]["phone_type"] = "None"
    embedding_npy = embedding.numpy()
    database[spkid]["embedding_1"] = embedding_npy
    database[spkid]["wav"] = wav_file_path
    database[spkid]["raw"] = raw_file_path

    database[spkid]["max_score"] = max_score
    database[spkid]["mean_score"] = mean_score
    database[spkid]["min_score"] = min_score
    database[spkid]["max_class_index"] = max_class_index

    database[spkid]["time"] = (datetime.now()).strftime("%Y-%m-%d %H:%M:%S")
    print(embedding_npy.shape)
    toRedis(r,embedding_npy,f'{max_class_index}_{spkid}')
    with open(database_filepath, 'wb') as f:
        pickle.dump(database, f)
    return True,phone_info

def get_embeddings(class_index):
    pass