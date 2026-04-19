import librosa
import numpy as np

def extract_features(file_path, sr=16000, n_mfcc=20):
    try:
        y, sr = librosa.load(file_path, sr=sr, mono=True)

        if len(y) == 0:
            return None

        y, _ = librosa.effects.trim(y, top_db=20)

        if len(y) == 0:
            return None

        mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc)
        delta = librosa.feature.delta(mfcc)
        delta2 = librosa.feature.delta(mfcc, order=2)

        features = np.concatenate([
            np.mean(mfcc, axis=1),
            np.std(mfcc, axis=1),
            np.mean(delta, axis=1),
            np.std(delta, axis=1),
            np.mean(delta2, axis=1),
            np.std(delta2, axis=1),
        ])

        return features.astype(np.float32)

    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return None