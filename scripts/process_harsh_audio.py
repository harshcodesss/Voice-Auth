import os
import numpy as np
import librosa
import soundfile as sf

INPUT_DIR = "dataset/custom_hindi/harsh_raw"
OUTPUT_DIR = "backend/data/custom_harsh_chunks"

CHUNK_DURATION = 10  # seconds
TARGET_SR = 16000

os.makedirs(OUTPUT_DIR, exist_ok=True)

for file in os.listdir(INPUT_DIR):
    if not file.endswith(".wav"):
        continue

    file_path = os.path.join(INPUT_DIR, file)

    y, sr = librosa.load(file_path, sr=TARGET_SR)

    chunk_samples = CHUNK_DURATION * sr
    total_chunks = len(y) // chunk_samples

    print(f"{file} → {total_chunks} chunks")

    for i in range(total_chunks):
        start = i * chunk_samples
        end = start + chunk_samples
        chunk = y[start:end]

        out_file = os.path.join(OUTPUT_DIR, f"harsh_chunk_{i+1}.wav")
        sf.write(out_file, chunk, sr)

print("✅ Harsh audio chunked!")