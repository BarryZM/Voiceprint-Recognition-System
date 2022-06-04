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
    r.set(n,encoded)
    return

def fromRedis(r,n):
    """Retrieve Numpy array from Redis key 'n'"""
    encoded = r.get(n)
    a = np.frombuffer(encoded, dtype=np.float32, offset=8)
    return a

# # Create 80x80 numpy array to store
# a0 = np.arange(6400,dtype=np.uint16).reshape(80,80) 


# # Store array a0 in Redis under name 'a0array'
# toRedis(r,a0,'a0array')

# # Retrieve from Redis
# a1 = fromRedis(r,'a0array')

# np.testing.assert_array_equal(a0,a1)

def get_all_embedding(index=-1):
    all_embedding = {}
    for key in r.keys():
        key = key.decode('utf-8')
        if "_" not in key:
            continue
        class_index = int(key.split("_")[0])
        if class_index == index or index == -1:
            spkid = key.split("_")[1]
            embedding_1 = fromRedis(r,key)
            all_embedding[spkid] = {"embedding_1":embedding_1}
        else:
            continue
    return all_embedding

def add_to_database(embedding,spkid,max_class_index):

    phone_info = getPhoneInfo(spkid)
    embedding_npy = embedding.numpy()
    toRedis(r,embedding_npy,f'{max_class_index}_{spkid}')
    
    return True,phone_info

def get_embeddings(class_index):
    pass