# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:40:43.000-05:00
# Desc  : preprocess wav file.(vad/resample/self test)

import torch
import torchaudio
import torchaudio.functional as F
import torchaudio.transforms as T
import os
from utils.scores import get_scores
import soundfile as sf
import time
import numpy as np
USE_ONNX = True

model, utils = torch.hub.load(repo_or_dir='./snakers4_silero-vad_master',
                             source='local',
                              model='silero_vad',
                              force_reload=False,
                              onnx=USE_ONNX)

(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

#, dtype=waveform.dtype)
       


def print_run_time(func):  
    def wrapper(*args, **kw):  
        local_time = time.time()  
        func(*args, **kw) 
        print('current Function [%s] run time is %.2f' % (func.__name__ ,time.time() - local_time))
    return wrapper 


def vad_and_upsample(wav_file,spkid,wav_length=90,savepath=None,channel=1):
    
    """vad and upsample to 16k.

    Args:
        wav_file (string): filepath of the uploaded wav file.
        channel (int, optional): which channel to use. Defaults to 0.

    Returns:
        torch.tensor: new wav tensor
    """

    # TODO:简化VAD操作
    local_time = time.time()

    wav, sr = sf.read(wav_file)
    print(f"read raw file: sr={sr} wav={len(wav)/sr}")
    
    # wav = read_audio(wav_file, sampling_rate=8000)
    if len(wav.shape)>1:

        if wav.shape[0]>sr*(7+wav_length):
            wav = torch.FloatTensor(wav[7*sr:(7+wav_length)*sr,channel])
        else:
            wav = torch.FloatTensor(wav[7*sr:,channel])
    else:
        if wav.shape[0]>sr*(7+wav_length):
            wav = torch.FloatTensor(wav[7*sr:(7+wav_length)*sr])
        else:
            wav = torch.FloatTensor(wav[7*sr:])
    print(wav.shape)
    
    if sr != 1600:
        resampler = T.Resample(sr, 16000)
        wav = resampler(wav)
    before_vad_length = len(wav)/sr
    
    speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=16000,window_size_samples=512)
    wav_torch = collect_chunks(speech_timestamps, wav)
    

    if savepath != None:

        spk_dir = os.path.join(savepath, str(spkid))
        os.makedirs(spk_dir, exist_ok=True)
        spk_filelist = os.listdir(spk_dir)
        speech_number = len(spk_filelist) + 1
        # receive wav file and save it to  ->  <receive_path>/<spk_id>/raw_?.webm
        save_name = f"preprocessed_{speech_number}.wav"
        final_save_path = os.path.join(spk_dir, save_name)

        save_audio(final_save_path,wav_torch, sampling_rate=16000)
    else:
        final_save_path = None
    
    after_vad_length = len(wav_torch)/16000.
    used_time = time.time() - local_time
    result = {
        "wav_torch":wav_torch,
        "before_length":before_vad_length,
        "after_length":after_vad_length,
        "save_path":final_save_path,
        "used_time":used_time

    }
    return result

def self_test(wav_torch, spkreg,similarity, sr=16000, min_length=20, similarity_limit=0.7):
    """Quality detection function, self-splitting into multiple fragments and then testing them in pairs.

    Args:
        wav_torch (torch.tensor): input wav
        spkreg (speechbarin.model): embedding model from speechbrain.
        similarity (function): similarity function
        sr (int, optional): sample rate. Defaults to 16000.
        split_num (int, optional): split wav to <num> fragments. Defaults to 3.
        min_length (int, optional): length(s) of each fragment. Defaults to 3.
        similarity_limit (float, optional): similarity limit for self-test. Defaults to 0.7.

    Returns:
        _type_: pass or not, message
    """
    local_time = time.time()
    # TODO：简化自我检测

    max_score = 0
    min_score = 1

    if len(wav_torch)/sr <= min_length:
        used_time = time.time() - local_time
        result = {
            "pass":False,
            "msg":f"Insufficient duration, the current duration is {len(wav_torch)/sr}s.",
            "max_score":0,
            "mean_score":0,
            "min_score":0,
            "used_time":used_time,
        }
        return result

    half_length = int(len(wav_torch)/2)
    tiny_wav1 = torch.tensor(wav_torch[half_length:]).unsqueeze(0)
    embedding1 = spkreg.encode_batch(tiny_wav1)[0][0]

    tiny_wav2 = torch.tensor(wav_torch[:half_length]).unsqueeze(0)
    embedding2 = spkreg.encode_batch(tiny_wav2)[0][0]
    score = similarity(embedding1, embedding2).numpy()
    max_score,mean_score,min_score = score,score,score
    used_time = time.time() - local_time

    if score < similarity_limit:
        print(f"Score:{min_score}")
        result = {
            "pass":False,
            "msg":f"Bad quality score:{min_score}.",
            "max_score":max_score,
            "mean_score":mean_score,
            "min_score":min_score,
            "used_time":used_time,
        }
        return result
    result = {
            "pass":True,
            "msg":"Qualified.",
            "max_score":max_score,
            "mean_score":mean_score,
            "min_score":min_score,
            "used_time":used_time,
        }
    return result
