# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:43:24.000-05:00
# Desc  : Save wav files.

import os
from re import U
import wget

def save_wav_from_file(file, spk, receive_path):
    """save wav file from post request.

    Args:
        file (request.file): wav file.
        spk (string): speack id
        receive_path (string): save path

    Returns:
        string: file path
    """
    
    spk_dir = os.path.join(receive_path, str(spk))
    os.makedirs(spk_dir, exist_ok=True)
    spk_filelist = os.listdir(spk_dir)
    speech_number = len(spk_filelist) + 1
    # receive wav file and save it to  ->  <receive_path>/<spk_id>/raw_?.webm
    save_name = f"raw_{speech_number}.webm"
    save_path = os.path.join(spk_dir, save_name)
    file.save(save_path)
    return save_path, speech_number

def save_wav_from_url(url, spk, receive_path):
    """save wav file from post request.

    Args:
        file (request.file): wav file.
        spk (string): speack id
        receive_path (string): save path

    Returns:
        string: file path
    """
    
    spk_dir = os.path.join(receive_path, str(spk))
    os.makedirs(spk_dir, exist_ok=True)
    spk_filelist = os.listdir(spk_dir)
    speech_number = len(spk_filelist) + 1
    # receive wav file and save it to  ->  <receive_path>/<spk_id>/raw_?.webm
    save_name = f"raw_{speech_number}.wav"
    
    
    if url.startswith("local:"):
        save_path = url.replace("local:", "")
    else:
        save_path = os.path.join(spk_dir, save_name)
        wget.download(url, save_path) # 下载

    return save_path, speech_number


def save_embedding():
    # !待实现
    pass