from features import extract_features

file_path = "../../data/processed/Speaker_0000/Speaker_0000_00001.wav"

features = extract_features(file_path)

print("Feature vector shape:", features.shape)
print(features)