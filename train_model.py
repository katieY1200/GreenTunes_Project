import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, accuracy_score
import joblib

np.random.seed(42)
N = 2000

frequency = np.random.uniform(5, 150, N)
amplitude = np.random.uniform(0.0, 1.0, N)
noise_level = np.random.uniform(0.0, 0.8, N)
duration_ms = np.random.uniform(0.5, 8.0, N)

labels = (
    (frequency >= 20) & (frequency <= 100) &
    (amplitude >= 0.75) &
    (noise_level <= 0.3) &
    (duration_ms >= 2.0)
).astype(int)

flip_mask = np.random.random(N) < 0.03
labels[flip_mask] = 1 - labels[flip_mask]

X = np.column_stack([frequency, amplitude, noise_level, duration_ms])
X_train, X_test, y_train, y_test = train_test_split(X, labels, test_size=0.2, random_state=42)

model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
model.fit(X_train, y_train)

y_pred = model.predict(X_test)
print(f"accuracy: {accuracy_score(y_test, y_pred):.4f}")
print(classification_report(y_test, y_pred, target_names=["정상", "이상"]))

joblib.dump(model, "model.pkl")
print("saved model.pkl")
