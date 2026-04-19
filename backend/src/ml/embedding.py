import torch
from speechbrain.inference import EncoderClassifier

classifier = EncoderClassifier.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb",
    savedir="tmp_model"
)

def get_embedding(audio_file):
    signal = classifier.load_audio(audio_file)
    embedding = classifier.encode_batch(signal)
    return embedding.squeeze().detach().numpy()