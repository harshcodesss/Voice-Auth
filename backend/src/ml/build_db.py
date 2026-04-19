import os
import numpy as np
import joblib

from embedding import get_embedding

DATA_PATH = "../../data/processed"
DB_PATH = "../../models/speaker_db.pkl"

speaker_db = {}

for speaker in os.listdir(DATA_PATH):
    speaker_path = os.path.join(DATA_PATH, speaker)

    if not os.path.isdir(speaker_path):
        continue

    embeddings = []

    for file in os.listdir(speaker_path):
        if file.endswith(".wav"):
            file_path = os.path.join(speaker_path, file)
            emb = get_embedding(file_path)
            embeddings.append(emb)

    if embeddings:
        speaker_db[speaker] = np.mean(embeddings, axis=0)

joblib.dump(speaker_db, DB_PATH)

print("✅ Speaker DB built!")