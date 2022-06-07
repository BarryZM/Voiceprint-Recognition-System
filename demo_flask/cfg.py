# -*- coding:utf-8 -*-
# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email : zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:48:31.000-05:00
# Desc  : Config file.

# Black database data {"spk_id":spk_id,"wav_file":wav_file_path,"embedding":embedding}
BLACK_LIST = "./wavs/database/blackbase.pkl"

# wav files save path
REGISTER_RAW_PATH = "./wavs/raw"
REGISTER_PREPROCESSED_PATH = "./wavs/preprocessed"
TEST_RAW_PATH = "./wavs/test/raw"
TEST_PREPROCESSED_PATH = "./wavs/test/preprocessed"

# black threshold: Determine whether it is in the black library
BLACK_TH = 0.80

# self test threshold
SELF_TEST = 1
SELF_TEST_TH = 0.6

# 记录手机号信息
LOG_PHONE_INFO = 1

# use wav length(s)
# 使用多长的音频(秒)
WAV_LENGTH = 90

# self test fragments number
TEST_SPLIT_NUM = 4

# self test min length(s) of each fragment
MIN_LENGTH = 5

AUTO_TESTING_MODE = True

MYSQL_DATABASE = "mysql://root:Nt3380518!zhaosheng123@zhaosheng.mysql.rds.aliyuncs.com:27546/si"
