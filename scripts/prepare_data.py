import os
import shutil
import numpy as np
import librosa
import soundfile as sf

INPUT_DIR = "dataset/kaggle"
OUTPUT_DIR = "backend/data/processed"

TARGET_SR = 16000
CHUNK_DURATION = 10   # seconds
CHUNKS_PER_FILE = 6   # 6 x 10 sec = 60 sec

# Start fresh
if os.path.exists(OUTPUT_DIR):
    shutil.rmtree(OUTPUT_DIR)
os.makedirs(OUTPUT_DIR, exist_ok=True)

for speaker in sorted(os.listdir(INPUT_DIR)):
    speaker_path = os.path.join(INPUT_DIR, speaker)

    if not os.path.isdir(speaker_path):
        continue

    output_speaker_path = os.path.join(OUTPUT_DIR, speaker)
    os.makedirs(output_speaker_path, exist_ok=True)

    chunk_count = 0

    for file in sorted(os.listdir(speaker_path)):
        if not file.lower().endswith(".wav"):
            continue

        file_path = os.path.join(speaker_path, file)

        try:
            y, sr = librosa.load(file_path, sr=TARGET_SR, mono=True)

            if len(y) == 0:
                continue

            total_samples = CHUNK_DURATION * CHUNKS_PER_FILE * TARGET_SR
            chunk_samples = CHUNK_DURATION * TARGET_SR

            # Pad or trim to exactly 60 seconds
            if len(y) < total_samples:
                y = np.pad(y, (0, total_samples - len(y)))
            else:
                y = y[:total_samples]

            base_name = os.path.splitext(file)[0]

            # Create 6 sequential non-overlapping 10-second chunks
            for i in range(CHUNKS_PER_FILE):
                start = i * chunk_samples
                end = start + chunk_samples
                chunk = y[start:end]

                out_file = os.path.join(
                    output_speaker_path,
                    f"{base_name}_chunk_{i+1}.wav"
                )
                sf.write(out_file, chunk, TARGET_SR)
                chunk_count += 1

        except Exception as e:
            print(f"Error processing {file_path}: {e}")

    print(f"{speaker}: {chunk_count} chunks created")

print("✅ 10-second chunk extraction done!")