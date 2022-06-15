# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:38:52.000-05:00
# Desc  : Get cosine scores of the spacify wav with all wavs in database.
import torch
import numpy as np

def get_scores(database,new_embedding,black_limit,similarity,top_num=10):
    return_results = {}
    results = []
    top_list = ""
    # Read embeddings in database
    for base_item in database:
        base_embedding = torch.tensor(database[base_item]["embedding_1"])
        results.append([similarity(base_embedding, new_embedding), base_item])
    results = sorted(results, key=lambda x:float(x[0])*(-1))
    return_results["best_score"] = float(np.array(results[0][0]))
    print(f"Best score:{results[0][0]}")

    if results[0][0] <= black_limit:
        return_results["inbase"] = 0
        print(f"\tNot in base, best score is {results[0][0]}")
        print(return_results)
        print(top_list)
        return return_results,top_list
    else:
        return_results["inbase"] = 1
        # top1-top10
        for index in range(top_num):
            return_results[f"top_{index+1}"] = f"{results[index][0].numpy():.5f}"
            return_results[f"top_{index+1}_id"] = str(results[index][1])
            top_list+=f"Top {index+1} 评分:{results[index][0].numpy():.2f} 说话人:{results[index][1]}<br/>"
    print(return_results)
    print(top_list)
    return return_results,top_list


def self_check(database,embedding,spkid,black_limit,similarity,top_num=10):
    results = []
    return_results = {}
    for base_item in database.keys():
        base_embedding = torch.tensor(database[base_item]["embedding_1"])
        results.append([similarity(base_embedding, embedding), base_item])
    results = sorted(results, key=lambda x:float(x[0])*(-1))
    best_score = float(np.array(results[0][0]))
    best_id = str(np.array(results[0][1]))
    return_results["best_score"] = best_score
    print(f"Spkid: {spkid} -> Best score:{results[0]}")

    inbase = (spkid in database.keys())
    if inbase:
        if best_score > black_limit:
            return_results["inbase"] = 1
            # top1-top10
            for index in range(top_num):
                if results[index][1] == spkid:
                    msg = f"在黑库中,正确,第{index+1}个命中了。得分:{results[index][0]},now_spk:{spkid},best score:{best_score},spk:{best_id}"
                    return True,1,msg
            msg = f"在黑库中,错误,但未命中,now_spk:{spkid},best score:{best_score},spk:{best_id}"
            return False,2,msg
        else:
            return True,3,f"在黑库中,错误,不满足阈值,now_spk:{spkid},best score:{best_score},spk:{best_id}"
    else:
        
        if best_score < black_limit:
            msg = f"不在黑库中,正确,now_spk:{spkid},best score:{best_score},spk:{best_id}"
            return True,4,msg
        else:
            msg = f"不在黑库中,错误,now_spk:{spkid},best score:{best_score},spk:{best_id}"
            return False,5,msg