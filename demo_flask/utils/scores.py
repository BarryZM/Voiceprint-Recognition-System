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