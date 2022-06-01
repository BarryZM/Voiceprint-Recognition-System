# models
from speechbrain.pretrained import SpeakerRecognition
import torch

# cosine
similarity = torch.nn.CosineSimilarity(dim=-1, eps=1e-6)

# embedding model
spkreg = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", savedir="./pretrained_ecapa")