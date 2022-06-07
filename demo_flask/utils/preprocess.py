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
USE_ONNX = True

model, utils = torch.hub.load(repo_or_dir='snakers4/silero-vad',
                              model='silero_vad',
                              force_reload=False,
                              onnx=USE_ONNX)

(get_speech_timestamps,
 save_audio,
 read_audio,
 VADIterator,
 collect_chunks) = utils

resampler = T.Resample(8000, 16000)#, dtype=waveform.dtype)
       


def print_run_time(func):  
    def wrapper(*args, **kw):  
        local_time = time.time()  
        func(*args, **kw) 
        print('current Function [%s] run time is %.2f' % (func.__name__ ,time.time() - local_time))
    return wrapper 


def vad_and_upsample(wav_file,spkid,wav_length,savepath=None,channel=0):
    
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
    
    # wav = read_audio(wav_file, sampling_rate=8000)
    
    if wav.shape[0]>sr*(7+wav_length):
        wav = torch.FloatTensor(wav[7*sr:(7+wav_length)*sr,1])
    else:
        wav = torch.FloatTensor(wav[7*sr:,1])
    print(wav.shape)
    wav = resampler(wav)
    before_vad_length = len(wav)/16000
    
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
    return wav_torch,before_vad_length,after_vad_length,final_save_path,before_vad_length,used_time

def self_test(wav_torch, spkreg,similarity, sr=16000, split_num=3, min_length=3, similarity_limit=0.7):
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
    split_num = 2
    min_length = 10

    scores_sum = 0
    scores_num = 0
    max_score = 0
    min_score = 1

    embedding_list = []
    wav_list = []
    if len(wav_torch)/sr <= split_num*min_length:
        used_time = time.time() - local_time
        return False, f"Insufficient duration, the current duration is {len(wav_torch)/sr}s.",0,0,0,used_time
    length = int(len(wav_torch)/split_num)

    for index in range(split_num):
        tiny_wav = torch.tensor(
            wav_torch[index*length:(index+1)*length]).unsqueeze(0)
        wav_list.append(tiny_wav)
        embedding_list.append(spkreg.encode_batch(tiny_wav)[0][0])

    # for embedding1 in embedding_list:
    #     for embedding2 in embedding_list:
    #         # TODO:这里的循环还可以优化。
    #         score = similarity(embedding1, embedding2)
    #         scores_sum += score
    #         scores_num += 1
    #         if score>= max_score:
    #             max_score = score
    #         if score<= min_score:
    #             min_score = score
            
    #         if score < similarity_limit:
    #             print(f"Score:{score}")
    #             return False, f"Bad quality score:{score}.",0,0,0
    # mean_score = scores_sum/scores_num
     
    embedding1 = embedding_list[0]
    embedding2 = embedding_list[0]
    score = similarity(embedding1, embedding2)
    max_score,mean_score,min_score = score,score,score
    used_time = time.time() - local_time
    # print(f"self-test used {time.time() - local_time}")
    if score < similarity_limit:
        print(f"Score:{score}")
        return False, f"Bad quality score:{score}.",0,0,0,used_time
    return True, "Qualified.", max_score,mean_score,min_score,used_time