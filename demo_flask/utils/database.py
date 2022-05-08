# Author: 𝕫𝕙𝕒𝕠𝕤𝕙𝕖𝕟𝕘
# Email: zhaosheng@nuaa.edu.cn
# Time  : 2022-05-06  19:53:59.000-05:00
# Desc  : utils about database
import pickle
def add_to_database(database,embedding,spkid,wav_file_path,database_filepath):
    """add new speaker or new wav to black databse

    Args:
        database (dict): old database
        embedding (torch.tensor): new embedding
        spkid (string): speak id
        wav_file_path (string): wav file path
    """
    if spkid in database.keys():
        return False
    else:
        database[spkid] = {}
    database[spkid]["embedding_1"] = embedding.numpy()
    database[spkid]["wav"] = wav_file_path
    with open(database_filepath, 'wb') as f:
        pickle.dump(database, f)
    return True