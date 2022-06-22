# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:43:24.000-05:00
# Desc  : Save wav files.

import os
from re import U
import wget
import subprocess
import shutil


def save_wav_from_file(file, spk, receive_path):
    """save wav file from post request.

    Args:
        file (request.file): wav file.
        spk (string): speack id
        receive_path (string): save path

    Returns:
        string: file path
    """
    if not receive_path:
        receive_path = "/tmp/"
    spk_dir = os.path.join(receive_path, str(spk))
    os.makedirs(spk_dir, exist_ok=True)
    spk_filelist = os.listdir(spk_dir)
    speech_number = len(spk_filelist) + 1
    # receive wav file and save it to  ->  <receive_path>/<spk_id>/raw_?.webm
    pid = os.getpid()
    save_name = f"raw_{speech_number}_{pid}.webm"
    save_path = os.path.join(spk_dir, save_name)
    save_path_wav = os.path.join(spk_dir, f"raw_{speech_number}_{pid}.wav")
    file.save(save_path)
    # conver to wav
    cmd = f"ffmpeg -i {save_path} -ac 1 -ar 8000 {save_path_wav}"
    subprocess.call(cmd, shell=True)
    return save_path_wav

def save_wav_from_url(url, spk, receive_path):
    """save wav file from post request.

    Args:
        file (request.file): wav file.
        spk (string): speack id
        receive_path (string): save path

    Returns:
        string: file path
    """
    if not receive_path:
        receive_path = "/tmp/"
    spk_dir = os.path.join(receive_path, str(spk))
    os.makedirs(spk_dir, exist_ok=True)
    spk_filelist = os.listdir(spk_dir)
    speech_number = len(spk_filelist) + 1
    # receive wav file and save it to  ->  <receive_path>/<spk_id>/raw_?.webm

    pid = os.getpid()
    save_name = f"raw_{speech_number}_{pid}.wav"

    if url.startswith("local:"):
        previous_path = url.replace("local:", "")
        save_path = os.path.join(spk_dir, save_name)
        shutil.copy(previous_path,save_path)
    else:
        save_path = os.path.join(spk_dir, save_name)
        wget.download(url, save_path)
        print(f"开始下载：{url}")
    print("下载完成")
    return save_path


def save_embedding():
    # !待实现
    pass