import joblib
import numpy as np

from embedding import get_embedding

DB_PATH = "../../models/speaker_db.pkl"

def cosine_similarity(a, b):
    return np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b))

def predict(file_path, threshold=0.7):
    db = joblib.load(DB_PATH)
    emb = get_embedding(file_path)

    best_speaker = None
    best_score = -1

    for speaker, ref_emb in db.items():
        score = cosine_similarity(emb, ref_emb)

        if score > best_score:
            best_score = score
            best_speaker = speaker

    if best_score < threshold:
        return "Unknown", best_score

    return best_speaker, best_score