"""
lightweight_classifier.py
A tiny TF-IDF + Logistic Regression grievance classifier — an alternative
to the zero-shot neural classifier (BART/DistilBART), for constrained
hosting environments (e.g. Render free tier, 512MB RAM).

Trained on a SYNTHETIC/TEMPLATE-GENERATED dataset (see
scripts/build_grievance_training_data.py) — not real farmer complaints.
Real labeled grievance data doesn't exist yet; replace when available.
Given the small dataset (~43 examples), treat confidence scores as
indicative, not precise — same honest caveat as the crop-loss model.
"""
import pandas as pd
import joblib
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "data", "grievance_training_data.csv")
MODEL_PATH = os.path.join(BASE_DIR, "saved_models", "grievance_classifier.pkl")
VECTORIZER_PATH = os.path.join(BASE_DIR, "saved_models", "grievance_vectorizer.pkl")

_model = None
_vectorizer = None


def train():
    df = pd.read_csv(DATA_PATH)

    vectorizer = TfidfVectorizer(max_features=500, ngram_range=(1, 2))
    X = vectorizer.fit_transform(df["text"])
    y = df["category"]

    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)

    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    joblib.dump(model, MODEL_PATH)
    joblib.dump(vectorizer, VECTORIZER_PATH)

    print(f"Trained on {len(df)} examples across {df['category'].nunique()} categories")
    print("Model size:", os.path.getsize(MODEL_PATH), "bytes")
    print("Vectorizer size:", os.path.getsize(VECTORIZER_PATH), "bytes")


def get_model():
    global _model, _vectorizer
    if _model is None:
        _model = joblib.load(MODEL_PATH)
        _vectorizer = joblib.load(VECTORIZER_PATH)
    return _model, _vectorizer


def classify(text: str):
    model, vectorizer = get_model()
    X = vectorizer.transform([text])
    probs = model.predict_proba(X)[0]
    classes = model.classes_

    best_idx = probs.argmax()
    return {
        "category": classes[best_idx],
        "confidence": round(float(probs[best_idx]) * 100, 1),
    }


if __name__ == "__main__":
    train()

    test_texts = [
        "My PM-KISAN payment has not arrived for 3 months",
        "Officer asked for bribe during document verification",
        "No rainfall in our area for a month",
    ]
    for t in test_texts:
        print(t, "->", classify(t))