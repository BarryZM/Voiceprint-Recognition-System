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
from sklearn.model_selection  import cross_val_score
from sklearn.neighbors import KNeighborsClassifier
from sklearn.cluster import SpectralClustering
from sklearn import metrics
import numpy as np
import os
from IPython import embed
import soundfile as sf
import subprocess
from sympy import I
import torch
from tqdm import tqdm
import pandas as pd
# models
from speechbrain.pretrained import SpeakerRecognition
similarity = torch.nn.CosineSimilarity(dim=-1, eps=1e-6)
spkreg = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", savedir="./pretrained_ecapa")
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


def self_test(wav_torch,time_limit=1,similarity_limit=0.7):
    # 1->时长不足1秒
    # 2->自我检验不合格
    # 3->合格
    if len(wav_torch)/16000 <= time_limit:
        return 1
    half_length = int(len(wav_torch)/2)
    tiny_wav1 = torch.tensor(wav_torch[half_length:]).unsqueeze(0)
    embedding1 = spkreg.encode_batch(tiny_wav1)[0][0]
    tiny_wav2 = torch.tensor(wav_torch[:half_length]).unsqueeze(0)
    embedding2 = spkreg.encode_batch(tiny_wav2)[0][0]
    score = similarity(embedding1, embedding2).numpy()
    if score < similarity_limit:
        return 2
    return 3

def vad_and_upsample(wav_file):
    wav, sr = sf.read(wav_file)
    wav = torch.from_numpy(wav).float()
    # print(wav.shape)
    before_vad_length = len(wav)/16000
    # print(f'转换前时长：{before_vad_length}')
    # wav = torch.tensor(wav,dtype=float)
    speech_timestamps = get_speech_timestamps(wav, model, sampling_rate=16000,window_size_samples=512)
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

# 格式转换、重采样以及编码（多线程）
def get_embedding_multi(wav_file_list):    
    items = wav_file_list
    print(items[0])
    pool = ThreadPool()
    pool.map(get_embedding_tiny, items)
    pool.close()
    pool.join()

def get_embedding_tiny(wav_file):
    file_name = wav_file.split('/')[-1].split('.')[0]
    try:
        wav_torch,after_vad_length,before_vad_length = vad_and_upsample(wav_file)
        now_embedding = spkreg.encode_batch(wav_torch).detach().numpy()[0][0]        
        embedding_npy = [True,now_embedding,file_name,after_vad_length,"合格"]
        np.save(f"/mnt/zhaosheng/m2n_test/embeddings_amr/{file_name}.npy",embedding_npy)
        return
    except Exception as e:
        print(e)
        embedding_npy = [False,0,file_name,0,"其他错误"]
        np.save(f"/mnt/zhaosheng/m2n_test/embeddings_amr_err/{file_name}.npy",embedding_npy)
        return

def preprocess_wav_file_multi(wav_file_list):
    items = wav_file_list
    print(items[0])
    pool = ThreadPool()
    pool.map(preprocess_wav_tiny, items)
    pool.close()
    pool.join()

def preprocess_wav_tiny(wav_file):
    file_name = wav_file.split('/')[-1].split('.')[0]
    try:
        wav_torch,after_vad_length,before_vad_length = vad_and_upsample(wav_file)
        self_test_result = self_test(wav_torch)
        if self_test_result == 3:
            now_embedding = spkreg.encode_batch(wav_torch).detach().numpy()[0][0]        
            embedding_npy = [self_test_result,now_embedding,file_name,before_vad_length,after_vad_length,"合格"]
            np.save(f"/mnt/zhaosheng/m2n_test/embeddings_0610/3/{file_name}.npy",embedding_npy)
            return
        elif self_test_result == 2:
            # 自我检验不合格
            now_embedding = spkreg.encode_batch(wav_torch).detach().numpy()[0][0]        
            embedding_npy = [self_test_result,now_embedding,file_name,before_vad_length,after_vad_length,"合格"]
            np.save(f"/mnt/zhaosheng/m2n_test/embeddings_0610/2/{file_name}.npy",embedding_npy)
            return
        elif self_test_result == 1:
            # 时长不足1秒
            now_embedding = spkreg.encode_batch(wav_torch).detach().numpy()[0][0]        
            embedding_npy = [self_test_result,now_embedding,file_name,before_vad_length,after_vad_length,"合格"]
            np.save(f"/mnt/zhaosheng/m2n_test/embeddings_0610/3/{file_name}.npy",embedding_npy)
            return
    except Exception as e:
        print(e)
        embedding_npy = [4,0,file_name,0,0,"其他错误"]
        np.save(f"/mnt/zhaosheng/m2n_test/embeddings_0610/4/{file_name}.npy",embedding_npy)
        return


# 获取编码向量
def get_embedding_list():
    # if os.path.exists("m2n_test.npy"):
    #     return np.load("m2n_test.npy",allow_pickle=True)
    embeddings = []
    npy_files = [os.path.join("/mnt/zhaosheng/m2n_test/embeddings/",file_name) for file_name in os.listdir("/mnt/zhaosheng/m2n_test/embeddings/")]
    for npy in npy_files:
        embeddings.append(np.load(npy,allow_pickle=True))
    embeddings = np.array(embeddings)
    #np.save("m2n_test.npy",embeddings)
    return embeddings

# 谱聚类
def m2n_spectral(wav_file_list):
    # get_embedding_multi(wav_file_list)
    A =get_embedding_list()

    Scores = [0]  # 存放轮廓系数,根据轮廓系数的计算公式，只有一个类簇时，轮廓系数为0
    Scores1 = [0]   # 存放AH系数,根据轮廓系数的计算公式，只有一个类簇时，系数为0
    for k in range(2,6):
        
        estimator = SpectralClustering(n_clusters=k,random_state=0,affinity='precomputed').fit_predict(A)
        Scores.append(metrics.silhouette_score(A, estimator, metric='euclidean'))
        # 为Score列表添加质量度量值
        Scores1.append(metrics.calinski_harabasz_score(A, estimator))
    print(Scores)
    print(Scores1)
    i = range(2, 7)
    plt.xlabel('k')
    plt.ylabel('value')
    plt.plot(i,Scores,'g.-',i,Scores1,'b.-')
    # silhouette_score是绿色（数值越大越好） calinski_harabasz_score是蓝色（数值越大越好）
    plt.show()

def get_embedding_lists(embeddings):
    print(embeddings[0])
    init_data = [[embeddings[0][1],f"/mnt/zhaosheng/m2n_test/wav/{embeddings[0][2]}.wav"]]
    embedding_lists = [init_data]
    class_number = 0
    result = {}

    for data in tqdm(embeddings[1:]):
        is_done = False
        now_embedding = data[1]
        now_filename = data[2]
        now_file_path =  f"/mnt/zhaosheng/m2n_test/wav/{now_filename}.wav"
        
        for class_index in result.keys():
            embedding_list = result[class_index]

            for data in embedding_list:
                embedding,file_path = data
                score = similarity(torch.from_numpy(now_embedding).float(),torch.from_numpy(embedding).float())
                if  score > 0.1:
                    result[class_index].append([now_embedding,now_file_path])
                    is_done = True
                    break
            if is_done:
                is_done = False
                continue
        embedding_lists.append([[now_embedding,now_file_path]])
        result[class_number] = [[now_embedding,now_file_path]]
        class_number+=1
        print(class_number)

    return embedding_lists

# cos手动聚类
def m2n(wav_file_list):
    # get_embedding_multi(wav_file_list)
    embeddings= get_embedding_list()
    # embed()
    embedding_lists = get_embedding_lists(embeddings)
    # return embedding_lists
    return np.array(embedding_lists,dtype=object)

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

def m2n_knn(wav_file_list):
    get_embedding_multi(wav_file_list)
    for time_limit in [1]:#[0.5,1,1.5,2,2.5,3]:#,1.5,2,2.5,3,5
        embeddings= get_embedding_list()

        embeddings_info_df = pd.DataFrame(np.load("./m2n_test.npy",allow_pickle=True), columns = ['pass','embedding','filename','after_vad_length','msg'])
        data = []
        files = []
        for embedding in embeddings:
            if embedding[3] > time_limit:
                data.append(embedding[1])
                files.append(embedding[2])
            
        data = np.array(data)
        print(data.shape)
        #k_list = [110,120,130,140,150,160,170,180,190,200]
    
        # for k in range(170,190):#k_list:
        k=186
        clustering = KMeans(n_clusters=k,random_state=5)
        #fit the dataset
        clustering.fit(data)
        # print(clustering.labels_)
        labels = clustering.labels_

        #TODO 计算cosine误差
        all_data = []
        for file,label in zip(files,labels):
            all_data.append([file,label])
        all_data = np.array(all_data)
        df = pd.DataFrame(all_data, columns = ['file','label'])
        err = calc_err(df,k,embeddings_info_df)
        print(f"time_limit= {time_limit} k = {k} Err={err}")


        # 复制文件
        result_path = "/mnt/zhaosheng/m2n_test/m2n_result_0610_001"
        no_class_save_path = os.path.join(result_path,"音频过短")
        os.makedirs(no_class_save_path,exist_ok=True)
        err_save_path = os.path.join(result_path,"音频读取错误")
        os.makedirs(err_save_path,exist_ok=True)



        all_files = [file.split(".")[0] for file in os.listdir("/mnt/zhaosheng/m2n_test/amr/Case01-20211230-144203") if "amr" in file]
        for file in all_files:
            if file not in files:
                file_path = f"/mnt/zhaosheng/m2n_test/amr/Case01-20211230-144203/{file}.amr"
                shutil.copy(file_path, no_class_save_path)
        for file,label in zip(files,labels):
            file_path = f"/mnt/zhaosheng/m2n_test/amr/Case01-20211230-144203/{file}.amr"
            save_path = os.path.join(result_path,str(label))
            os.makedirs(save_path,exist_ok=True)
            shutil.copy(file_path, save_path)

if __name__ == "__main__":
    root = "/mnt/zhaosheng/m2n_test/amr/Case01-20211230-144203"
    wav_file_list = [os.path.join(root,filename) for filename in os.listdir(root) if "amr" in filename]
    preprocess_wav_file(wav_file_list)
    m2n_knn(wav_file_list)
