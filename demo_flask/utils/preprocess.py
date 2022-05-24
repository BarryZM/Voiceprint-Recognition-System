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
USE_ONNX = False
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
           
def vad_and_upsample(wav_file,spkid,savepath=None,channel=0):
    """vad and upsample to 16k.

    Args:
        wav_file (string): filepath of the uploaded wav file.
        channel (int, optional): which channel to use. Defaults to 0.

    Returns:
        torch.tensor: new wav tensor
    """
    wav, sr = sf.read(wav_file)
    # wav = read_audio(wav_file, sampling_rate=8000)
    print(wav.shape)
    wav = torch.FloatTensor(wav[7*sr:,1])
    before_vad_length = len(wav)/sr
    
    speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=8000,window_size_samples=512)
    wav_torch = collect_chunks(speech_timestamps, wav)
    resampled_waveform = resampler(wav_torch)
    if savepath != None:

        spk_dir = os.path.join(savepath, str(spkid))
        os.makedirs(spk_dir, exist_ok=True)
        spk_filelist = os.listdir(spk_dir)
        speech_number = len(spk_filelist) + 1
        # receive wav file and save it to  ->  <receive_path>/<spk_id>/raw_?.webm
        save_name = f"preprocessed_{speech_number}.wav"
        final_save_path = os.path.join(spk_dir, save_name)

        save_audio(final_save_path,resampled_waveform, sampling_rate=16000)
    else:
        final_save_path = None
    after_vad_length = len(resampled_waveform)/16000.
    return resampled_waveform,before_vad_length,after_vad_length,final_save_path

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
    scores_sum = 0
    scores_num = 0
    max_score = 0
    min_score = 1

    embedding_list = []
    wav_list = []
    if len(wav_torch)/sr <= split_num*min_length:
        return False, f"Insufficient duration, the current duration is {len(wav_torch)/sr}s.",0,0,0
    length = int(len(wav_torch)/split_num)

    for index in range(split_num):
        tiny_wav = torch.tensor(
            wav_torch[index*length:(index+1)*length]).unsqueeze(0)
        wav_list.append(tiny_wav)
        embedding_list.append(spkreg.encode_batch(tiny_wav)[0][0])
    for embedding1 in embedding_list:
        for embedding2 in embedding_list:
            # TODO:这里的循环还可以优化。
            score = similarity(embedding1, embedding2)
            scores_sum += score
            scores_num += 1
            if score>= max_score:
                max_score = score
            if score<= min_score:
                min_score = score
            
            if score < similarity_limit:
                print(f"Score:{score}")
                return False, f"Bad quality score:{score}.",0,0,0
    mean_score = scores_sum/scores_num
    return True, "Qualified.", max_score,mean_score,min_score