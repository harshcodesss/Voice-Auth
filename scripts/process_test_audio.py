import os
import librosa
import soundfile as sf
import random

INPUT_DIR = "backend/data/test_voice"
OUTPUT_DIR = "backend/data/test_voice/processed"
CLIP_DURATION = 5  # seconds

os.makedirs(OUTPUT_DIR, exist_ok=True)

for speaker in os.listdir(INPUT_DIR):
    speaker_path = os.path.join(INPUT_DIR, speaker)

    if not os.path.isdir(speaker_path):
        continue

    output_speaker_path = os.path.join(OUTPUT_DIR, speaker)
    os.makedirs(output_speaker_path, exist_ok=True)

    for file in os.listdir(speaker_path):
        if not file.endswith(".wav"):
            continue

        file_path = os.path.join(speaker_path, file)

        try:
            y, sr = librosa.load(file_path, sr=16000)

            clip_samples = CLIP_DURATION * sr

            if len(y) < clip_samples:
                continue

            start = random.randint(0, len(y) - clip_samples)
            y = y[start:start + clip_samples]

            output_file = os.path.join(output_speaker_path, file)
            sf.write(output_file, y, sr)

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

print("✅ Test audio processed!")