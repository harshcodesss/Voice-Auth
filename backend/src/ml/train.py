import os
import numpy as np
import joblib
import random

from features import extract_features
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.svm import SVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, classification_report, confusion_matrix

DATA_PATH = "../../data/processed"
MODEL_PATH = "../../models/speaker_model.pkl"

X = []
y = []

for speaker in os.listdir(DATA_PATH):
    speaker_path = os.path.join(DATA_PATH, speaker)

    if not os.path.isdir(speaker_path):
        continue

    for file in os.listdir(speaker_path):
        if file.lower().endswith(".wav"):
            file_path = os.path.join(speaker_path, file)
            features = extract_features(file_path)

            if features is not None:
                X.append(features)
                y.append(speaker)

# Convert to numpy
X = np.array(X)
y = np.array(y)

print("Total samples:", len(X))
print("Feature shape:", X.shape[1] if len(X) > 0 else "N/A")

# 🔥 Print class distribution
unique, counts = np.unique(y, return_counts=True)
print("\nClass Distribution:")
for u, c in zip(unique, counts):
    print(f"{u}: {c}")

if len(X) < 10:
    raise ValueError("Not enough data to train the model.")

# 🔥 Shuffle dataset
indices = np.arange(len(X))
np.random.shuffle(indices)
X = X[indices]
y = y[indices]

# Train-test split
X_train, X_test, y_train, y_test = train_test_split(
    X,
    y,
    test_size=0.2,
    random_state=42,
    stratify=y
)

# Model pipeline
model = Pipeline([
    ("scaler", StandardScaler()),
    ("svc", SVC(
        kernel="rbf",
        C=10,
        gamma="scale",
        probability=True,
        class_weight="balanced",
        random_state=42
    ))
])

# Train
model.fit(X_train, y_train)

# Predict
y_pred = model.predict(X_test)

# Evaluate
accuracy = accuracy_score(y_test, y_pred)
print(f"\nModel Accuracy: {accuracy:.4f}")

print("\nClassification Report:")
print(classification_report(y_test, y_pred))

print("Confusion Matrix:")
print(confusion_matrix(y_test, y_pred))

# Save model
os.makedirs("../../models", exist_ok=True)
joblib.dump(model, MODEL_PATH)

print("\n✅ Model saved at:", MODEL_PATH)