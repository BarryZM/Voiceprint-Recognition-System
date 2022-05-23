# -*- coding:utf-8 -*-
# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email : zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:48:31.000-05:00
# Desc  : Config file.

# Black database data {"spk_id":spk_id,"wav_file":wav_file_path,"embedding":embedding}
BLACK_LIST = "/si-server/blackbase.pkl"

# test wav files save path
SAVE_PATH = "/si-server/demo_flask/saved_wavs"

# black base wav files save path
BASE_WAV_PATH = "/si-server/demo_flask/base_wavs"

# black threshold: Determine whether it is in the black library
BLACK_TH = 0.7

# self test threshold
SELF_TEST_TH = 0.6

# self test fragments number
TEST_SPLIT_NUM = 4

# self test min length(s) of each fragment
MIN_LENGTH = 5

