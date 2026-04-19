import os
from predict_embed import predict

TEST_DIR = "../../data/test_voice"

for speaker in sorted(os.listdir(TEST_DIR)):
    speaker_path = os.path.join(TEST_DIR, speaker)

    if not os.path.isdir(speaker_path):
        continue

    print(f"\n===== Testing: {speaker} =====")

    for file in os.listdir(speaker_path):
        if file.endswith(".wav"):
            file_path = os.path.join(speaker_path, file)

            pred, score = predict(file_path)

            print(f"{file} → Predicted: {pred} | Similarity: {score:.3f}")