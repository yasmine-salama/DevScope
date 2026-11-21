import json
import os
from typing import Dict, Any

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

from .feature_engineering import compute_scores, load_developers_dataframe


def _skills_tokenizer(s):
    """Tokenizer de niveau module pour `skills_joined` (picklable)."""
    if isinstance(s, str):
        return [t.strip() for t in s.split(",") if t.strip()]
    return []


def _get_model_store_path() -> str:
    base = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    path = os.path.join(base, "instance", "ml")
    os.makedirs(path, exist_ok=True)
    return os.path.join(path, "best_model.joblib")


def train_and_evaluate(save_path: str = None, top_percentile: float = 0.7, user_id: int = None) -> Dict[str, Any]:
    """Entraîne plusieurs classifieurs et sauvegarde le meilleur.

    - Crée un label `high_quality` basé sur `global_score` (seuil top_percentile)
    - Teste LogisticRegression, KNN, DecisionTree, RandomForest
    - Retourne métriques et chemin du modèle sauvegardé
    """
    df = load_developers_dataframe(user_id=user_id)
    if df.empty:
        return {"error": "No developer data available"}

    df = compute_scores(df)
    if len(df) < 4:
        return {"error": "Not enough developer data available to train a reliable model"}

    # Binarize target: top X% by global_score
    thresh = df["global_score"].quantile(top_percentile)
    df["high_quality"] = (df["global_score"] >= thresh).astype(int)
    if df["high_quality"].nunique() < 2:
        return {"error": "Training data contains only one target class"}

    numeric_features = [
        "followers_count",
        "repos_count",
        "contributions_last_year",
        "account_age_days",
        "last_activity_days",
        "total_skills",
    ]

    X = df[numeric_features + ["skills_joined"]]
    y = df["high_quality"]

    stratify = y if y.value_counts().min() >= 2 else None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=stratify)

    # Preprocessing: TF-IDF for skills, scaling for numeric
    skills_vectorizer = TfidfVectorizer(tokenizer=_skills_tokenizer, token_pattern=None)

    preprocessor = ColumnTransformer(
        transformers=[
            ("skills", skills_vectorizer, "skills_joined"),
            ("num", StandardScaler(), numeric_features),
        ],
        remainder="drop",
    )

    candidates = {
        "LogisticRegression": LogisticRegression(max_iter=1000),
        "KNN": KNeighborsClassifier(),
        "RandomForest": RandomForestClassifier(n_estimators=100),
    }

    results = {}
    best_model = None
    best_score = -1.0
    best_info = None

    for name, clf in candidates.items():
        pipe = Pipeline([("pre", preprocessor), ("clf", clf)])
        try:
            pipe.fit(X_train, y_train)
        except Exception as exc:
            results[name] = {"error": str(exc)}
            continue

        y_pred = pipe.predict(X_test)
        acc = accuracy_score(y_test, y_pred)
        prec = precision_score(y_test, y_pred, zero_division=0)
        rec = recall_score(y_test, y_pred, zero_division=0)
        f1 = f1_score(y_test, y_pred, zero_division=0)
        cm = confusion_matrix(y_test, y_pred).tolist()

        metrics = {"accuracy": acc, "precision": prec, "recall": rec, "f1": f1, "confusion_matrix": cm}
        results[name] = metrics

        if f1 > best_score:
            best_score = f1
            best_model = pipe
            best_info = {"name": name, "metrics": metrics}

    if best_model is None:
        return {"error": "No model trained", "results": results}

    model_path = save_path or _get_model_store_path()
    # Save pipeline and metadata
    payload = {"pipeline": best_model, "model_name": best_info["name"], "metrics": best_info["metrics"], "numeric_features": numeric_features}
    joblib.dump(payload, model_path)

    return {"model_path": model_path, "best": best_info, "results": results}


def load_saved_model(path: str = None) -> Dict[str, Any]:
    """Charge le modèle sauvegardé et retourne le payload (pipeline + metadata)."""
    model_path = path or _get_model_store_path()
    if not os.path.exists(model_path):
        return {}
    try:
        payload = joblib.load(model_path)
        return payload
    except Exception:
        return {}
