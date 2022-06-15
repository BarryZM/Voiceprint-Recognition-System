import sys
sys.path.append('/VAF-System/demo_flask/utils')

# models
from speechbrain.pretrained import SpeakerRecognition
import torch

# cosine
similarity = torch.nn.CosineSimilarity(dim=-1, eps=1e-6)

# embedding model
spkreg = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", savedir="./pretrained_ecapa")

from preprocess import vad_and_upsample,self_test

from sklearn.cluster import SpectralClustering
from sklearn import metrics
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
# # models
# from speechbrain.pretrained import SpeakerRecognition
# import torch

# # cosine
# similarity = torch.nn.CosineSimilarity(dim=-1, eps=1e-6)

# # embedding model
# spkreg = SpeakerRecognition.from_hparams(
#     source="speechbrain/spkrec-ecapa-voxceleb", savedir="./pretrained_ecapa")


# 谱聚类

def m2n_spectral(wav_file_list):
    total_length = len(wav_file_list)
    pass_num = 0
    result = {}
    embeddings = []
    for wav_file in wav_file_list:
        spkid = ""
        wav_length = 999 # 不截断
        wav_torch,before_vad_length,after_vad_length,final_save_path,before_vad_length,used_time = vad_and_upsample(wav_file,spkid,wav_length,save_wavs=False,savepath=None,channel=0)
        pass_test,_ = self_test(wav_torch, spkreg,similarity, sr=16000, similarity_limit=0.8)
        if pass_test:
            pass_num += 1
            print(wav_torch.shape)
            embeddings.append(wav_torch)

    Scores = [0]  # 存放轮廓系数,根据轮廓系数的计算公式，只有一个类簇时，轮廓系数为0
    Scores1 = [0]   # 存放AH系数,根据轮廓系数的计算公式，只有一个类簇时，系数为0
    A = np.array(embeddings)
    # A = np.array([
    #             [0, 0, 0, 20, 0, 40],
    #             [0, 0, 57, 0, 0, 57],
    #             [0, 0, 0, 0, 57, 57],
    #             [0, 0, 0, 0, 0, 40],
    #             [57, 0, 0, 0, 0, 114],
    #             [0, 0, 0, 0, 0, 0]
    #             ])
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


def append_to_embedding(embedding_lists,wav_torch):
    now_embedding = spkreg(wav_torch)
    for embedding_list in embedding_lists:
        for embedding in embedding_list:
            if similarity(now_embedding,embedding) > 0.82:
                embedding_list.append(now_embedding)
                return embedding_lists
    embedding_lists.append([now_embedding])
    return embedding_lists
                


def m2n(wav_file_list):
    total_length = len(wav_file_list)
    pass_num = 0
    result = {}
    embedding_lists = []
    for wav_file in wav_file_list:

        spkid = ""
        wav_length = 999 # 不截断
        wav_torch,before_vad_length,after_vad_length,final_save_path,before_vad_length,used_time = vad_and_upsample(wav_file,spkid,wav_length,save_wavs=False,savepath=None,channel=0)
        pass_test,_ = self_test(wav_torch, spkreg,similarity, sr=16000, similarity_limit=0.8)
        if pass_test:
            pass_num += 1
            append_to_embedding(embedding_lists,wav_torch)
    return embedding_lists


if __name__ == "__main__":
    wav_list = []
    root = "/mnt/zhaosheng/m2n_test"
    for spk_path in os.listdir(root):
        spk_path = os.path.join(root,spk_path)
        sence_path = [os.path.join(spk_path,uuid) for uuid in os.listdir(spk_path)]
        for child_path in sence_path:
            wav_list+=[os.path.join(child_path,wav_file) for wav_file in os.listdir(child_path)]
    print(wav_list)