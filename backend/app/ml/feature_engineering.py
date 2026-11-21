from datetime import datetime
from typing import List

import numpy as np
import pandas as pd

from ..extensions import db
from ..models.developer import Developer, UserDeveloper


def load_developers_dataframe(user_id: int = None) -> pd.DataFrame:
    """Charge les développeurs depuis la base et retourne un DataFrame nettoyé.

    Colonnes retournées (exemples):
    - id, username, followers_count, repos_count, contributions_last_year
    - account_age_days, last_activity_days
    - skills_list (liste), skills_joined (str séparée par ',')

    La fonction gère les valeurs manquantes et les doublons.
    """
    query = Developer.query
    if user_id is not None:
        query = query.join(UserDeveloper, UserDeveloper.developer_id == Developer.id).filter(
            UserDeveloper.user_id == user_id
        )
    developers = query.all()
    rows = []
    now = datetime.utcnow()

    for dev in developers:
        skills = [ds.skill.name for ds in getattr(dev, "dev_skills", []) if getattr(ds, "skill", None)]

        created_at = dev.created_at or dev.updated_at or now
        last_act = dev.last_activity_at or created_at

        account_age_days = (now - created_at).days if created_at else 0
        last_activity_days = (now - last_act).days if last_act else 9999

        rows.append(
            {
                "id": dev.id,
                "platform": dev.platform,
                "username": dev.username,
                "display_name": dev.display_name,
                "followers_count": int(dev.followers_count or 0),
                "repos_count": int(dev.repos_count or 0),
                "contributions_last_year": int(dev.contributions_last_year or 0),
                "account_age_days": int(account_age_days),
                "last_activity_days": int(last_activity_days),
                "skills_list": skills,
                "skills_joined": ",".join(skills) if skills else "",
            }
        )

    df = pd.DataFrame(rows)

    if df.empty:
        # Return an empty but typed DataFrame
        cols = [
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
        return pd.DataFrame(columns=cols)

    # Remove duplicates by (platform, username)
    df = df.drop_duplicates(subset=["platform", "username"])

    # Fill missing numeric values and ensure correct dtypes
    for col in ["followers_count", "repos_count", "contributions_last_year", "account_age_days", "last_activity_days"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    # Normalize text columns
    df["username"] = df["username"].astype(str)

    return df


def _minmax(s: pd.Series) -> pd.Series:
    denom = (s.max() - s.min()) if (s.max() - s.min()) != 0 else 1.0
    return (s - s.min()) / denom


def compute_scores(df: pd.DataFrame) -> pd.DataFrame:
    """Ajoute des features dérivées et un `global_score`.

    Scores calculés:
    - total_skills: nombre de technos
    - popularity_score: combinaison followers/repo
    - activity_score: contributions récentes
    - contribution_score: repos + contributions
    - experience_score: âge du compte en années
    - global_score: combinaison normalisée

    Retourne une copie du DataFrame avec colonnes ajoutées.
    """
    if df.empty:
        return df

    df = df.copy()

    df["total_skills"] = df["skills_list"].apply(lambda x: len(x) if isinstance(x, list) else 0)

    popularity_raw = df["followers_count"].astype(float) * 0.7 + df["repos_count"].astype(float) * 0.3
    activity_raw = df["contributions_last_year"].astype(float)
    contribution_raw = df["repos_count"].astype(float) + df["contributions_last_year"].astype(float)
    experience_raw = df["account_age_days"].astype(float) / 365.0

    df["popularity_score"] = _minmax(popularity_raw)
    df["activity_score"] = _minmax(activity_raw)
    df["contribution_score"] = _minmax(contribution_raw)
    df["experience_score"] = _minmax(experience_raw)
    df["skills_score"] = _minmax(df["total_skills"].astype(float))

    # Weighted global score (tunable)
    df["global_score"] = (
        0.3 * df["popularity_score"]
        + 0.2 * df["activity_score"]
        + 0.2 * df["contribution_score"]
        + 0.2 * df["experience_score"]
        + 0.1 * df["skills_score"]
    )

    return df


def top_skills(df: pd.DataFrame, top_n: int = 20) -> List[tuple]:
    """Retourne les compétences les plus fréquentes sous forme (skill, count)."""
    if df.empty:
        return []
    s = df["skills_list"].explode().value_counts().head(top_n)
    return list(s.items())
