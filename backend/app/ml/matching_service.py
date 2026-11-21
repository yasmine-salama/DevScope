from typing import List, Dict, Any, Optional

import pandas as pd

from ..models.developer import Developer
from .feature_engineering import load_developers_dataframe, compute_scores
from .model_training import load_saved_model
from .prediction_service import batch_predict


def _skill_match_details(required: List[str], candidate_skills: List[str]) -> Dict[str, Any]:
    req_list = [s.strip() for s in required if s]
    req_set = set([s.lower() for s in req_list])
    cand_list = [s.strip() for s in (candidate_skills or []) if s]
    cand_set = set([s.lower() for s in cand_list])

    if not req_set:
        return {"match": 0.0, "matched": [], "missing": []}

    matched = list(req_set.intersection(cand_set))
    missing = list(req_set.difference(cand_set))
    match_score = len(matched) / len(req_set)

    # return original-cased matched/missing when possible
    def original_case(items):
        res = []
        for it in items:
            for s in cand_list + req_list:
                if s and s.lower() == it:
                    res.append(s)
                    break
            else:
                res.append(it)
        return res

    return {"match": match_score, "matched": original_case(matched), "missing": original_case(missing)}


def match_job(
    title: str,
    required_technologies: List[str],
    required_skills: List[str],
    experience_level: str = "mid",
    top_n: int = 10,
    weight_skill: float = 0.5,
    weight_ml: float = 0.3,
    weight_experience: float = 0.2,
    live_profiles: Optional[List[Dict[str, Any]]] = None,
    user_id: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Retourne un classement détaillé de profils pour une offre donnée.

    Retourne des items avec: matched/missing skills, skill_match, ml_score, experience_match, final_score.
    Weights sont normalisées si nécessaire.
    """
    # Load base data
    df = load_developers_dataframe(user_id=user_id)

    # Prepare live profiles DataFrame (if any)
    live_df = None
    if live_profiles:
        try:
            live_df = pd.DataFrame(live_profiles)
        except Exception:
            live_df = None

    # Combine and compute scores
    if (df is None or df.empty) and (live_df is None or live_df.empty):
        return []

    if df is not None and not df.empty:
        df = compute_scores(df)
    if live_df is not None and not live_df.empty:
        # Ensure expected columns
        expected = [
            "id",
            "platform",
            "username",
            "display_name",
            "followers_count",
            "repos_count",
            "contributions_last_year",
            "account_age_days",
            "last_activity_days",
            "skills_list",
            "skills_joined",
        ]
        for c in expected:
            if c not in live_df.columns:
                live_df[c] = 0 if c.endswith("_count") or c.endswith("days") else "" if c.endswith("_joined") else []
        live_df = compute_scores(live_df)

    # Final DataFrame for scoring
    if df is None or df.empty:
        combined = live_df
    elif live_df is None or live_df.empty:
        combined = df
    else:
        combined = pd.concat([df, live_df], ignore_index=True, sort=False)

    # Normalize weights
    total_w = (weight_skill or 0.0) + (weight_ml or 0.0) + (weight_experience or 0.0)
    if total_w <= 0:
        weight_skill, weight_ml, weight_experience = 0.6, 0.4, 0.0
        total_w = 1.0
    weight_skill /= total_w
    weight_ml /= total_w
    weight_experience /= total_w

    # Prepare rows for ML prediction (use combined DataFrame)
    numeric_cols = [
        "followers_count",
        "repos_count",
        "contributions_last_year",
        "account_age_days",
        "last_activity_days",
        "total_skills",
    ]
    rows = combined[numeric_cols + ["skills_joined"]].to_dict(orient="records")

    payload = load_saved_model()
    ml_preds = batch_predict(rows, payload) if payload else [{"probability": 0.0, "prediction": 0} for _ in rows]

    # experience thresholds (normalized feature)
    exp_thresholds = {"junior": 0.2, "mid": 0.5, "senior": 0.75}
    req_all = (required_technologies or []) + (required_skills or [])

    candidates = []
    for i, row in combined.iterrows():
        cand_skills = row.get("skills_list") or []
        details = _skill_match_details(req_all, cand_skills)
        skill_score = float(details.get("match", 0.0))

        ml_score = float(ml_preds[i]["probability"]) if i < len(ml_preds) else 0.0

        cand_exp = float(row.get("experience_score", 0.0))
        thr = exp_thresholds.get(experience_level, 0.5)
        experience_match = float(cand_exp / thr) if thr > 0 and cand_exp < thr else 1.0
        experience_match = max(0.0, min(1.0, experience_match))

        final_score = weight_skill * skill_score + weight_ml * ml_score + weight_experience * experience_match

        candidates.append(
            {
                "id": int(row.get("id") or -1),
                "platform": row.get("platform") if "platform" in row else None,
                "profile_url": row.get("profile_url") if "profile_url" in row else None,
                "username": row.get("username"),
                "display_name": row.get("display_name"),
                "skill_match": round(skill_score, 4),
                "matched_skills": details.get("matched", []),
                "missing_skills": details.get("missing", []),
                "ml_score": round(ml_score, 4),
                "experience_score": round(cand_exp, 4),
                "experience_match": round(experience_match, 4),
                "final_score": round(final_score, 4),
                "skills": cand_skills,
                "global_score": float(row.get("global_score", 0.0)),
            }
        )

    candidates = sorted(candidates, key=lambda x: x["final_score"], reverse=True)
    return candidates[:top_n]
