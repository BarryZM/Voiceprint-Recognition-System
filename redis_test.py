import struct
import redis
import numpy as np
import pickle
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

if __name__ == "__main__":

    with open("/home/zhaosheng/VAF-System/demo_flask/wavs/database/blackbase.pkl", 'rb') as base:
        black_database = pickle.load(base)
    a = black_database["15151832002"]["embedding_1"]
    toRedis(r,a,"141_15151832002")
    b = fromRedis(r,"141_15151832002")
    print(a==b)
    print(a)
    print(b)
    