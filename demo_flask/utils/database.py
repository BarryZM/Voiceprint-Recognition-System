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
import cfg

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

def get_all_embedding(blackbase="redis",class_index=-1):
    if blackbase  != 'redis':
        # all_spker_embedding = np.load(cfg.BLACK_BASE_SAVE_PATH,allow_pickle=True)
        # # load
        with open(cfg.BLACK_BASE, 'rb') as f:
            all_spker_embedding = pickle.load(f)
        all_embedding = {}
        for key in all_spker_embedding.keys():
            if "_" not in key:
                continue
            class_index_now = int(key.split("_")[0])
            if class_index_now == class_index or class_index == -1:
                spkid = key.split("_")[1]
                embedding_1 = all_spker_embedding[key]["embedding_1"]
                all_embedding[spkid] = {"embedding_1":embedding_1}
            else:
                continue
        return all_embedding

    else:
        r = redis.Redis(host=cfg.REDIS["host"], port=cfg.REDIS["port"], db=cfg.REDIS["db"])
        all_embedding = {}
        for key in r.keys():
            key = key.decode('utf-8')
            if "_" not in key:
                continue
            class_index_now = int(key.split("_")[0])
            if class_index_now == class_index or class_index == -1:
                spkid = key.split("_")[1]
                embedding_1 = fromRedis(r,key)
                all_embedding[spkid] = {"embedding_1":embedding_1}
            else:
                continue
        return all_embedding

def add_to_database(blackbase,embedding,spkid,max_class_index,log_phone_info):
    if log_phone_info:
        phone_info = getPhoneInfo(spkid)
    else:
        phone_info = {}
    embedding_npy = embedding.numpy()

    if blackbase == 'redis':
        r = redis.Redis(host=cfg.REDIS["host"], port=cfg.REDIS["port"], db=cfg.REDIS["db"])    
        toRedis(r,embedding_npy,f'{max_class_index}_{spkid}')
    else:
        pass
        
    return True,phone_info

def save_redis_to_pkl():
    r = redis.Redis(host=cfg.REDIS["host"], port=cfg.REDIS["port"], db=cfg.REDIS["db"])
    all_embedding = {}
    for key in r.keys():
        key = key.decode('utf-8')
        spkid = key
        embedding_1 = fromRedis(r,key)
        all_embedding[spkid] = {"embedding_1":embedding_1}
    with open(cfg.BLACK_BASE, 'wb') as f:
        pickle.dump(all_embedding, f, pickle.HIGHEST_PROTOCOL)


def get_embeddings(class_index):
    pass

if __name__ == "__main__":
    save_redis_to_pkl()