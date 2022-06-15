# Email : zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:48:31
# Desc  : Config file.

# wav files save path
SAVE_WAVS = False

# savepath
REGISTER_RAW_PATH = "./wavs/raw"
REGISTER_PREPROCESSED_PATH = "./wavs/preprocessed"
TEST_RAW_PATH = "./wavs/test/raw"
TEST_PREPROCESSED_PATH = "./wavs/test/preprocessed"

# black threshold: Determine whether it is in the black library
BLACK_TH = 0.81

# self test threshold
SELF_TEST = 1
SELF_TEST_TH = 0.81

# 记录手机号信息
LOG_PHONE_INFO = 1

# use wav length(s)
# 使用多长的音频(秒)
WAV_LENGTH = 120

# self test fragments number
TEST_SPLIT_NUM = 4

# self test min length(s) of each fragment
MIN_LENGTH = 5

# self test
AUTO_TESTING_MODE = True

# Mysql
MYSQL_DATABASE = "mysql://root:Nt3380518!zhaosheng123@47.114.192.153:27546/si"#zhaosheng.mysql.rds.aliyuncs.com
MYSQL_DATABASE_DICT = {
            "host": "47.114.192.153",
            "port": 27546,
            "db": "si",
            "username": "root",
            "passwd": "Nt3380518!zhaosheng123"
    }

# Blackbase
# Black database data {"spk_id":spk_id,"wav_file":wav_file_path,"embedding":embedding}
BLACK_BASE_SAVE_TYPE = "redis" # "redis" or "pkl"
BLACK_BASE_SAVE_PATH = "./wavs/database/blackbase.pkl"
REDIS_DATABASE_HOST = '127.0.0.1'
REDIS_DATABASE_PORT = 6379
REDIS_DATABASE_DB = 0