import struct
import redis
import numpy as np
import pickle
import sys
sys.path.append("/VAF-System/demo_flask")
import cfg

# Redis connection
r = redis.Redis(host=cfg.REDIS["host"], port=cfg.REDIS["port"], db=cfg.REDIS["db"])


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

   with open("/VAF-System/demo_flask/wavs/database/blackbase.pkl", 'rb') as base:
      black_database = pickle.load(base)
   keys = black_database.keys()
   for k in keys:
      print(k)
      break
   a = black_database["54_18567343505"]["embedding_1"]
   toRedis(r,a,"141_15151832002")
   b = fromRedis(r,"141_15151832002")
   print(a==b)