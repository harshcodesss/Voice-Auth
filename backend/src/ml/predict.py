import os
import sys
import joblib
import numpy as np
from collections import Counter

from features import extract_features

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
MODEL_PATH = os.path.join(PROJECT_ROOT, "backend", "models", "speaker_model.pkl")


def load_model():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model not found at: {MODEL_PATH}")
    return joblib.load(MODEL_PATH)


MODEL = load_model()


def predict_speaker(file_path, conf_threshold=0.9, gap_threshold=0.2):
    features = extract_features(file_path)
    if features is None:
        return "Unknown", 0.0, False, 0.0

    features = features.reshape(1, -1)

    predicted_speaker = MODEL.predict(features)[0]
    probabilities = MODEL.predict_proba(features)[0]

    confidence = float(np.max(probabilities))

    sorted_probs = np.sort(probabilities)[::-1]
    top1 = sorted_probs[0]
    top2 = sorted_probs[1] if len(sorted_probs) > 1 else 0.0
    gap = float(top1 - top2)

    if confidence < conf_threshold or gap < gap_threshold:
        return "Unknown", confidence, False, gap

    return predicted_speaker, confidence, True, gap


def predict_folder(folder_path, conf_threshold=0.9, gap_threshold=0.2):
    wav_files = [
        f for f in sorted(os.listdir(folder_path))
        if f.lower().endswith(".wav")
    ]

    if not wav_files:
        print(f"No wav files found in: {folder_path}")
        return

    chunk_predictions = []
    chunk_confidences = []
    chunk_gaps = []

    for file in wav_files:
        file_path = os.path.join(folder_path, file)
        predicted, confidence, known, gap = predict_speaker(
            file_path,
            conf_threshold=conf_threshold,
            gap_threshold=gap_threshold
        )

        status = "Known ✅" if known else "Unknown ❌"
        print(
            f"File: {file} | Predicted: {predicted} | "
            f"Confidence: {confidence:.2f} | Gap: {gap:.2f} | {status}"
        )

        chunk_predictions.append(predicted)
        chunk_confidences.append(confidence)
        chunk_gaps.append(gap)

    known_predictions = [p for p in chunk_predictions if p != "Unknown"]

    print("\n--- Folder Vote Summary ---")
    if not known_predictions:
        print("Final: Unknown ❌")
        return

    vote_counts = Counter(known_predictions)
    final_label, votes = vote_counts.most_common(1)[0]

    total_chunks = len(wav_files)
    vote_ratio = votes / total_chunks
    avg_conf = float(np.mean(chunk_confidences))
    avg_gap = float(np.mean(chunk_gaps))

    if vote_ratio >= 0.4 and avg_conf >= 0.85:
        print(f"Final: {final_label} ✅")
        print(f"Vote Ratio: {vote_ratio:.2f} | Avg Confidence: {avg_conf:.2f} | Avg Gap: {avg_gap:.2f}")
    else:
        print("Final: Unknown ❌")
        print(f"Vote Ratio: {vote_ratio:.2f} | Avg Confidence: {avg_conf:.2f} | Avg Gap: {avg_gap:.2f}")


def test_directory(test_dir, conf_threshold=0.9, gap_threshold=0.2):
    if not os.path.exists(test_dir):
        print(f"Test directory not found: {test_dir}")
        return

    subdirs = [
        d for d in sorted(os.listdir(test_dir))
        if os.path.isdir(os.path.join(test_dir, d))
    ]

    if subdirs:
        for speaker in subdirs:
            speaker_path = os.path.join(test_dir, speaker)
            print(f"\n===== Testing folder: {speaker} =====")
            predict_folder(
                speaker_path,
                conf_threshold=conf_threshold,
                gap_threshold=gap_threshold
            )
    else:
        print("\n===== Testing single folder =====")
        predict_folder(
            test_dir,
            conf_threshold=conf_threshold,
            gap_threshold=gap_threshold
        )


if __name__ == "__main__":
    example_file = os.path.join(
        PROJECT_ROOT,
        "backend",
        "data",
        "processed",
        "Speaker_0000",
        "Speaker_0000_chunk_1.wav"
    )

    if len(sys.argv) > 1:
        input_path = sys.argv[1]

        if os.path.isdir(input_path):
            test_directory(input_path)
        else:
            predicted, confidence, known, gap = predict_speaker(input_path)
            print(f"Predicted Speaker: {predicted}")
            print(f"Confidence: {confidence:.2f}")
            print(f"Gap: {gap:.2f}")
            print(f"Status: {'Known ✅' if known else 'Unknown ❌'}")
    else:
        predicted, confidence, known, gap = predict_speaker(example_file)
        print(f"Predicted Speaker: {predicted}")
        print(f"Confidence: {confidence:.2f}")
        print(f"Gap: {gap:.2f}")
        print(f"Status: {'Known ✅' if known else 'Unknown ❌'}")