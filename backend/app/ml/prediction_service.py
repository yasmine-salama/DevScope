from typing import Dict, Any, List

from .model_training import load_saved_model


def predict_profile_quality(developer_row: Dict[str, Any], model_payload: Dict = None) -> Dict[str, Any]:
    """Prédit si un profil est de haute qualité (probabilité et label).

    `developer_row` doit contenir les mêmes champs que la sortie de feature_engineering X (numeric + skills_joined)
    """
    payload = model_payload or load_saved_model()
    if not payload:
        return {"error": "No model available"}

    pipeline = payload.get("pipeline")
    if pipeline is None:
        return {"error": "Invalid model payload"}

    X = [developer_row]
    try:
        proba = pipeline.predict_proba(X)[0][1]
        pred = int(proba >= 0.5)
        return {"probability": float(proba), "prediction": pred}
    except Exception as e:
        return {"error": str(e)}


def batch_predict(df_rows: List[Dict[str, Any]], model_payload: Dict = None) -> List[Dict[str, Any]]:
    payload = model_payload or load_saved_model()
    if not payload:
        return []
    pipeline = payload.get("pipeline")
    try:
        X = df_rows
        probs = pipeline.predict_proba(X)
        return [{"probability": float(p[1]), "prediction": int(p[1] >= 0.5)} for p in probs]
    except Exception:
        return []
