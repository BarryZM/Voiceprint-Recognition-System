# ██╗██╗███╗   ██╗████████╗
# ██║██║████╗  ██║╚══██╔══╝
# ██║██║██╔██╗ ██║   ██║
# ██║██║██║╚██╗██║   ██║
# ██║██║██║ ╚████║   ██║
# ╚═╝╚═╝╚═╝  ╚═══╝   ╚═╝
# @Time    : 2022-06-09  15:07:42
# @Author  : 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# @email   : zhaosheng@nuaa.edu.cn
# @Blog    : http://iint.icu/
# @File    : /VAF-System/demo_flask/classify.py
# @Describe: classify raw arm/wav/mp3 files.

import shutil
from sklearn.cluster import KMeans 
from multiprocessing.dummy import Pool as ThreadPool
import numpy as np
import os
from IPython import embed
import torch
from tqdm import tqdm
import pandas as pd
import soundfile as sf
import torch
from sklearn.model_selection  import cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cluster import SpectralClustering
from sklearn import metrics
import soundfile as sf
import subprocess
from sympy import I
from multiprocessing.dummy import Pool as ThreadPool
import numpy as np
import os

# from utils import vad_and_upsample,self_test,get_embeddings,calc_err
from speechbrain.pretrained import SpeakerRecognition

similarity = torch.nn.CosineSimilarity(dim=-1, eps=1e-6)
spkreg = SpeakerRecognition.from_hparams(source="speechbrain/spkrec-ecapa-voxceleb")
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



def self_test(wav_torch,time_limit=1,similarity_limit=0.1):
    # 1->时长不足1秒
    # 2->自我检验不合格
    # 3->合格
    if len(wav_torch)/16000 <= time_limit:
        return 1,0
    half_length = int(len(wav_torch)/2)
    tiny_wav1 = torch.tensor(wav_torch[half_length:]).unsqueeze(0)
    embedding1 = spkreg.encode_batch(tiny_wav1)[0][0]
    tiny_wav2 = torch.tensor(wav_torch[:half_length]).unsqueeze(0)
    embedding2 = spkreg.encode_batch(tiny_wav2)[0][0]
    score = similarity(embedding1, embedding2).numpy()
    if score < similarity_limit:
        print(score)
        return 2,score
    return 3,score

def vad_and_upsample(wav_file):
    wav, sr = sf.read(wav_file)
    wav = torch.from_numpy(wav).float()
    # print(wav.shape)
    before_vad_length = len(wav)/16000
    # print(f'转换前时长：{before_vad_length}')
    # wav = torch.tensor(wav,dtype=float)
    speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=sr)#window_size_samples=512
    wav_torch = collect_chunks(speech_timestamps, wav)
    after_vad_length = len(wav_torch)/16000.
    # print(f'转换后时长：{after_vad_length}')
    return wav_torch,after_vad_length,before_vad_length

def amr2wav(amr_file,sr=16000):
    wav_file = amr_file.replace(".amr",".wav")
    if os.path.exists(wav_file):
        pass
    else:
        cmd = f"ffmpeg -i {amr_file} -ar {sr} {wav_file}"
        print(f" Run: {cmd}")
        subprocess.call(cmd, shell=True)

def calc_err(df,k,embeddings_info_df):
    total_err =[]
    for i in range(k):
        embedding_list = []
        files = list(df[df['label']==str(int(i))]["file"])
        for file in files:
            # print(file)
            embedding = list(embeddings_info_df[embeddings_info_df['filename']==file]["embedding"])[0]
            embedding_list.append(embedding)
        
        for embedding_index in range(len(embedding_list)):
            for embedding_index_2 in range(embedding_index+1,len(embedding_list)):
                # print(f"{embedding_index} - {embedding_index_2}")
                if embedding_index == embedding_index_2:
                    continue
                total_err.append(similarity(torch.from_numpy(embedding_list[embedding_index]).float(),torch.from_numpy(embedding_list[embedding_index_2]).float()))

    return np.mean(np.array(total_err))

def get_embeddings(embeddings_path="/mnt/zhaosheng/m2n_test/embeddings_0610/3",npy_path="m2n_test_0610.npy",reload=True):
    reload = True
    if reload or (not os.path.exists(npy_path)):
        embeddings = []
        npy_files = [os.path.join(embeddings_path,file_name) for file_name in os.listdir(embeddings_path)]
        for npy in npy_files:
            embeddings.append(np.load(npy,allow_pickle=True))
        embeddings = np.array(embeddings)
        np.save(npy_path,embeddings)
    else:
        embeddings=np.load(npy_path,allow_pickle=True)
    return embeddings

def preprocess_wav_file_multi(wav_file_list):
    items = wav_file_list
    print(items[0])
    pool = ThreadPool()
    pool.map(preprocess_wav_tiny, items)
    pool.close()
    pool.join()

def preprocess_wav_tiny(wav_file):
    os.makedirs(f"/mnt/zhaosheng/m2n_test/embeddings_0610/1",exist_ok=True)
    os.makedirs(f"/mnt/zhaosheng/m2n_test/embeddings_0610/2",exist_ok=True)
    os.makedirs(f"/mnt/zhaosheng/m2n_test/embeddings_0610/3",exist_ok=True)
    os.makedirs(f"/mnt/zhaosheng/m2n_test/embeddings_0610/4",exist_ok=True)
    file_name = wav_file.split('/')[-1].split('.')[0]
    try:
        wav_torch,after_vad_length,before_vad_length = vad_and_upsample(wav_file)
        self_test_result,score = self_test(wav_torch)
        if self_test_result == 3:
            now_embedding = spkreg.encode_batch(wav_torch).detach().numpy()[0][0]        
            embedding_npy = [self_test_result,now_embedding,file_name,before_vad_length,after_vad_length,score,"合格"]
            np.save(f"/mnt/zhaosheng/m2n_test/embeddings_0610/3/{file_name}.npy",embedding_npy)
            return
        elif self_test_result == 2:
            # 自我检验不合格
            now_embedding = spkreg.encode_batch(wav_torch).detach().numpy()[0][0]        
            embedding_npy = [self_test_result,now_embedding,file_name,before_vad_length,after_vad_length,score,"自我检验不合格"]
            np.save(f"/mnt/zhaosheng/m2n_test/embeddings_0610/2/{file_name}.npy",embedding_npy)
            return
        elif self_test_result == 1:
            # 时长不足1秒
            now_embedding = spkreg.encode_batch(wav_torch).detach().numpy()[0][0]        
            embedding_npy = [self_test_result,now_embedding,file_name,before_vad_length,after_vad_length,score,"时长不足1秒"]
            np.save(f"/mnt/zhaosheng/m2n_test/embeddings_0610/1/{file_name}.npy",embedding_npy)
            return
    except Exception as e:
        print(e)
        print('read err')
        embedding_npy = [4,0,file_name,0,0,0,"其他错误"]
        np.save(f"/mnt/zhaosheng/m2n_test/embeddings_0610/4/{file_name}.npy",embedding_npy)
        return

def m2n_knn(embeddings):
    embeddings_info_df = pd.DataFrame(np.load("./m2n_test_0610.npy",allow_pickle=True), columns = ['self_test','embedding','filename','before_vad_length','after_vad_length','score','msg'])
    embeddings_info_df= embeddings_info_df[(embeddings_info_df['score']>0.2) & (embeddings_info_df['after_vad_length']>1)]
    data = list(embeddings_info_df["embedding"])
    files = list(embeddings_info_df["filename"])    
    data = np.array(data)
    print(data.shape)

    # k_list = [28]
    for k in [10]:
        clustering = KMeans(n_clusters=k,random_state=5)
        clustering.fit(data)
        labels = clustering.labels_

        #TODO 计算cosine误差
        all_data = []
        for file,label in zip(files,labels):
            all_data.append([file,label])
        all_data = np.array(all_data)
        df = pd.DataFrame(all_data, columns = ['file','label'])
        err = calc_err(df,k,embeddings_info_df)
        print(f"k = {k} Err={err}")


        # 复制文件
        result_path = f"/mnt/zhaosheng/m2n_test/m2n_result_0610_result03_k{k}"
        no_class_save_path = os.path.join(result_path,"音频过短")
        os.makedirs(no_class_save_path,exist_ok=True)
        err_save_path = os.path.join(result_path,"音频质量不合格")
        os.makedirs(err_save_path,exist_ok=True)
        err_save_path_2 = os.path.join(result_path,"音频质量不合格")
        os.makedirs(err_save_path_2,exist_ok=True)


        too_short_files = [file.split('.')[0] for file in os.listdir("/mnt/zhaosheng/m2n_test/embeddings_0610/1/") if "npy" in file]
        not_pass_files = [file.split('.')[0] for file in os.listdir("/mnt/zhaosheng/m2n_test/embeddings_0610/2/") if "npy" in file]
        load_err_files = [file.split('.')[0] for file in os.listdir("/mnt/zhaosheng/m2n_test/embeddings_0610/4/") if "npy" in file]
        all_files = [file.split(".")[0] for file in os.listdir("/mnt/zhaosheng/m2n_test/amr/Case01-20211230-144203") if "amr" in file]
        for file in all_files:
            if file not in files:
                if file in too_short_files:
                    file_path = f"/mnt/zhaosheng/m2n_test/amr/Case01-20211230-144203/{file}.amr"
                    shutil.copy(file_path, no_class_save_path)
                    continue
                elif file in not_pass_files:
                    file_path = f"/mnt/zhaosheng/m2n_test/amr/Case01-20211230-144203/{file}.amr"
                    shutil.copy(file_path, err_save_path_2)
                    continue
                else:
                    file_path = f"/mnt/zhaosheng/m2n_test/amr/Case01-20211230-144203/{file}.amr"
                    shutil.copy(file_path, err_save_path)
                    continue
        for file,label in zip(files,labels):
            file_path = f"/mnt/zhaosheng/m2n_test/amr/Case01-20211230-144203/{file}.amr"
            save_path = os.path.join(result_path,str(label))
            os.makedirs(save_path,exist_ok=True)
            shutil.copy(file_path, save_path)

if __name__ == "__main__":
    root = "/mnt/zhaosheng/m2n_test/wav/"
    wav_file_list = [os.path.join(root,filename) for filename in os.listdir(root) if "wav" in filename]
    # preprocess_wav_file_multi(wav_file_list)
    embeddings= get_embeddings(reload=True)
    m2n_knn(embeddings)
