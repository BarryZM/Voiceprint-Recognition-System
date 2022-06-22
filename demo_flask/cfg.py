TESTING_MODE = False



# 原始文件的保存路径，为 None 不保存
RAW_FILE_PATH = None # "/VAF-System/demo_flask/wavs/raw"

# 预处理(vad+上采样)后文件的保存路径，为 None 不保存
VAD_FILE_PATH = None # "/VAF-System/demo_flask/wavs/preprocessed"

# 黑库阈值
BLACK_TH = 0.81

# VAD后的音频最小时长
MIN_LENGTH = 20

# 自我检测阈值(<=0,表示不进行自我检测)
SELF_TEST_TH = 0.81
# 1:最基本 2:适中 3:最严格
SELF_TEST_MODE = 1

# 是否记录手机号信息
LOG_PHONE_INFO = False

# 使用多长的音频进行推理判断(秒)
# 仅对推理过程有效，对注册过程无效
WAV_LENGTH = 120
WAV_CHANNEL = 1

# self test
AUTO_TESTING_MODE = True

# Mysql配置
MYSQL = {
            "host": "47.114.192.153",
            "port": 27546,
            "db": "si",
            "username": "root",
            "passwd": "Nt3380518!zhaosheng123"
    }
# Redis配置
REDIS = {
    "host":'127.0.0.1',
    "port":6379,
    "db":0
}

# 黑库文件路径(='redis' 则使用redis服务)
BLACK_BASE = "redis" # "./wavs/database/blackbase.pkl"