import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pandas as pd
import plotly.express as px
from sqlalchemy import func

from ..extensions import db
from ..models import DevSkill, Developer, EtlRun, Favorite, Skill, UserDeveloper


def _developer_query(user_id: Optional[int]):
    query = Developer.query
    if not user_id:
        return query.filter(False)
    return query.join(UserDeveloper, UserDeveloper.developer_id == Developer.id).filter(
        UserDeveloper.user_id == user_id
    )


def _developer_id_query(user_id: Optional[int]):
    if not user_id:
        return db.session.query(UserDeveloper.developer_id).filter(False)
    return db.session.query(UserDeveloper.developer_id).filter(UserDeveloper.user_id == user_id)


def _fig_json(fig) -> Dict:
    return json.loads(fig.to_json())


def dashboard_summary(user_id: Optional[int]) -> Dict:
    dev_ids = _developer_id_query(user_id)
    total_profiles = _developer_query(user_id).with_entities(func.count(Developer.id)).scalar() or 0
    total_skills = (
        db.session.query(func.count(func.distinct(Skill.id)))
        .join(DevSkill, DevSkill.skill_id == Skill.id)
        .filter(DevSkill.developer_id.in_(dev_ids))
        .scalar()
        or 0
    )
    active_30d = (
        _developer_query(user_id).with_entities(func.count(Developer.id))
        .filter(Developer.last_activity_at.isnot(None))
        .filter(Developer.last_activity_at >= (datetime.utcnow() - timedelta(days=30)))
        .scalar()
        or 0
    )

    favorites_count = 0
    if user_id:
        favorites_count = (
            db.session.query(func.count(Favorite.developer_id))
            .filter(Favorite.user_id == user_id)
            .scalar()
            or 0
        )

    with_location = (
        _developer_query(user_id).with_entities(func.count(Developer.id))
        .filter(Developer.location.isnot(None))
        .filter(func.length(func.trim(Developer.location)) > 0)
        .scalar()
        or 0
    )
    with_bio = (
        _developer_query(user_id).with_entities(func.count(Developer.id))
        .filter(Developer.bio.isnot(None))
        .filter(func.length(func.trim(Developer.bio)) > 0)
        .scalar()
        or 0
    )

    most_active = (
        _developer_query(user_id).order_by(Developer.last_activity_at.desc().nullslast(), Developer.repos_count.desc())
        .limit(8)
        .all()
    )

    recent_collected = (
        _developer_query(user_id).order_by(
            Developer.created_at.desc().nullslast(),
            Developer.updated_at.desc(),
        )
        .limit(8)
        .all()
    )

    top_developers = _developer_query(user_id).order_by(Developer.followers_count.desc(), Developer.repos_count.desc()).limit(8).all()

    last_etl = (
        db.session.query(EtlRun)
        .filter(EtlRun.user_id == user_id)
        .order_by(EtlRun.started_at.desc())
        .first()
    )

    return {
        "kpis": {
            "total_profiles": int(total_profiles),
            "total_skills": int(total_skills),
            "favorites_count": int(favorites_count),
            "with_location_pct": int(round((with_location / max(int(total_profiles), 1)) * 100)),
            "with_bio_pct": int(round((with_bio / max(int(total_profiles), 1)) * 100)),
            "active_profiles_estimate": int(active_30d),
        },
        "most_active_profiles": [
            {
                "id": d.id,
                "platform": d.platform,
                "username": d.username,
                "display_name": d.display_name,
                "avatar_url": d.avatar_url,
                "repos_count": d.repos_count,
                "followers_count": d.followers_count,
                "last_activity_at": d.last_activity_at.isoformat() if d.last_activity_at else None,
            }
            for d in most_active
        ],
        "recent_collected_profiles": [
            {
                "id": d.id,
                "platform": d.platform,
                "username": d.username,
                "display_name": d.display_name,
                "avatar_url": d.avatar_url,
                "location": d.location,
                "created_at": d.created_at.isoformat() if d.created_at else None,
                "updated_at": d.updated_at.isoformat() if d.updated_at else None,
            }
            for d in recent_collected
        ],
        "top_developers": [
            {
                "id": d.id,
                "platform": d.platform,
                "username": d.username,
                "display_name": d.display_name,
                "avatar_url": d.avatar_url,
                "location": d.location,
                "followers_count": d.followers_count,
                "repos_count": d.repos_count,
            }
            for d in top_developers
        ],
        "etl_last_run": (
            {
                "id": last_etl.id,
                "status": last_etl.status,
                "source": last_etl.source,
                "query": last_etl.query,
                "extracted_count": last_etl.extracted_count,
                "transformed_count": last_etl.transformed_count,
                "loaded_count": last_etl.loaded_count,
                "created_count": int(getattr(last_etl, "created_count", 0) or 0),
                "updated_count": int(getattr(last_etl, "updated_count", 0) or 0),
                "linked_count": int(getattr(last_etl, "linked_count", 0) or 0),
                "duplicates_removed": int(getattr(last_etl, "duplicates_removed", 0) or 0),
                "missing_values_filled": int(getattr(last_etl, "missing_values_filled", 0) or 0),
                "error_count": int(getattr(last_etl, "error_count", 0) or 0),
                "started_at": last_etl.started_at.isoformat() if last_etl.started_at else None,
                "finished_at": last_etl.finished_at.isoformat() if last_etl.finished_at else None,
            }
            if last_etl
            else None
        ),
    }


def dashboard_charts(user_id: Optional[int] = None) -> Dict:
    dev_ids = _developer_id_query(user_id)
    rows = (
        db.session.query(Skill.name.label("skill"), func.sum(DevSkill.score).label("score"))
        .join(DevSkill, DevSkill.skill_id == Skill.id)
        .filter(DevSkill.developer_id.in_(dev_ids))
        .group_by(Skill.name)
        .order_by(func.sum(DevSkill.score).desc())
        .limit(12)
        .all()
    )

    df_top = pd.DataFrame(rows, columns=["skill", "score"])
    if df_top.empty:
        df_top = pd.DataFrame([{"skill": "Aucune donnée", "score": 0}])

    fig_top = px.bar(
        df_top,
        x="skill",
        y="score",
        title="Technologies principales",
        template="plotly_white",
    )

    devs = _developer_query(user_id).with_entities(Developer.platform, Developer.last_activity_at).all()
    df_dev = pd.DataFrame(devs, columns=["platform", "last_activity_at"])
    if not df_dev.empty:
        df_dev["last_activity_at"] = pd.to_datetime(df_dev["last_activity_at"], errors="coerce")
        df_dev = df_dev.dropna(subset=["last_activity_at"])

    if df_dev.empty:
        fig_time = px.line(
            pd.DataFrame([{"month": "Aucune donnée", "count": 0}]),
            x="month",
            y="count",
            title="Activité dans le temps",
            template="plotly_white",
        )
    else:
        df_dev["month"] = df_dev["last_activity_at"].dt.to_period("M").astype(str)
        df_time = df_dev.groupby("month").size().reset_index(name="count").sort_values("month")
        fig_time = px.line(df_time, x="month", y="count", markers=True, title="Activité dans le temps", template="plotly_white")

    if df_dev.empty:
        fig_platform = px.pie(
            pd.DataFrame([{"platform": "Aucune donnée", "count": 0}]),
            names="platform",
            values="count",
            title="Répartition par plateforme",
            template="plotly_white",
        )
    else:
        df_platform = df_dev.groupby("platform").size().reset_index(name="count")
        fig_platform = px.pie(df_platform, names="platform", values="count", title="Répartition par plateforme", template="plotly_white")

    loc_rows = _developer_query(user_id).with_entities(Developer.location).all()
    df_loc = pd.DataFrame(loc_rows, columns=["location"])
    if not df_loc.empty:
        df_loc["location"] = df_loc["location"].fillna("").astype(str)
        df_loc["bucket"] = df_loc["location"].apply(lambda x: (x.split(",")[-1].strip() if "," in x else x.strip()) or "Inconnu")
        df_loc = df_loc[df_loc["bucket"].str.len() > 0]
        df_loc = df_loc.groupby("bucket").size().reset_index(name="count").sort_values("count", ascending=False).head(12)
    if df_loc.empty:
        df_loc = pd.DataFrame([{"bucket": "Aucune donnée", "count": 0}])
    fig_loc = px.bar(df_loc, x="bucket", y="count", title="Répartition géographique", template="plotly_white")

    growth_rows = _developer_query(user_id).with_entities(Developer.created_at, Developer.updated_at).all()
    df_g = pd.DataFrame(growth_rows, columns=["created_at", "updated_at"])
    if not df_g.empty:
        df_g["date"] = pd.to_datetime(df_g["created_at"]).fillna(pd.to_datetime(df_g["updated_at"]))
        df_g = df_g.dropna(subset=["date"])
    if df_g.empty:
        fig_growth = px.line(pd.DataFrame([{"month": "Aucune donnée", "count": 0}]), x="month", y="count", title="Croissance des profils", template="plotly_white")
    else:
        df_g["month"] = df_g["date"].dt.to_period("M").astype(str)
        df_growth = df_g.groupby("month").size().reset_index(name="count").sort_values("month")
        fig_growth = px.area(df_growth, x="month", y="count", title="Croissance des profils", template="plotly_white")

    scatter_rows = _developer_query(user_id).with_entities(
        Developer.username,
        Developer.followers_count,
        Developer.repos_count,
        Developer.location,
    ).all()
    df_scatter = pd.DataFrame(scatter_rows, columns=["username", "followers", "repositories", "location"])
    if df_scatter.empty:
        df_scatter = pd.DataFrame([{"username": "Aucune donnée", "followers": 0, "repositories": 0, "location": "Inconnu"}])
    df_scatter["location"] = df_scatter["location"].fillna("Inconnu").replace("", "Inconnu")
    fig_influence = px.scatter(
        df_scatter,
        x="repositories",
        y="followers",
        hover_name="username",
        color="location",
        size=df_scatter["followers"].clip(lower=1),
        title="Followers vs dépôts",
        template="plotly_white",
    )

    activity_rows = _developer_query(user_id).with_entities(Developer.last_activity_at).all()
    df_activity = pd.DataFrame(activity_rows, columns=["last_activity_at"])
    if not df_activity.empty:
        now = pd.Timestamp.utcnow().tz_localize(None)
        dates = pd.to_datetime(df_activity["last_activity_at"], errors="coerce")
        age_days = (now - dates).dt.days
        df_activity["bucket"] = pd.cut(
            age_days,
            bins=[-1, 30, 90, 180, 365, 10_000],
            labels=["0-30 jours", "31-90 jours", "91-180 jours", "181-365 jours", "365+ jours"],
        )
        df_activity["bucket"] = df_activity["bucket"].astype("object").fillna("Inconnu")
        df_activity = df_activity.groupby("bucket").size().reset_index(name="count")
    if df_activity.empty:
        df_activity = pd.DataFrame([{"bucket": "Aucune donnée", "count": 0}])
    fig_freshness = px.bar(
        df_activity,
        x="bucket",
        y="count",
        title="Fraîcheur d'activité",
        template="plotly_white",
    )

    total_profiles = _developer_query(user_id).with_entities(func.count(Developer.id)).scalar() or 0
    denominator = max(int(total_profiles), 1)
    completeness = pd.DataFrame(
        [
            {
                "field": "Localisation",
                "coverage": round(
                    (
                        _developer_query(user_id).with_entities(func.count(Developer.id))
                        .filter(Developer.location.isnot(None))
                        .filter(func.length(func.trim(Developer.location)) > 0)
                        .scalar()
                        or 0
                    )
                    / denominator
                    * 100
                ),
            },
            {
                "field": "Bio",
                "coverage": round(
                    (
                        _developer_query(user_id).with_entities(func.count(Developer.id))
                        .filter(Developer.bio.isnot(None))
                        .filter(func.length(func.trim(Developer.bio)) > 0)
                        .scalar()
                        or 0
                    )
                    / denominator
                    * 100
                ),
            },
            {
                "field": "Date d'activité",
                "coverage": round(
                    (
                        _developer_query(user_id).with_entities(func.count(Developer.id))
                        .filter(Developer.last_activity_at.isnot(None))
                        .scalar()
                        or 0
                    )
                    / denominator
                    * 100
                ),
            },
            {
                "field": "Avatar",
                "coverage": round(
                    (
                        _developer_query(user_id).with_entities(func.count(Developer.id))
                        .filter(Developer.avatar_url.isnot(None))
                        .filter(func.length(func.trim(Developer.avatar_url)) > 0)
                        .scalar()
                        or 0
                    )
                    / denominator
                    * 100
                ),
            },
        ]
    )
    fig_completeness = px.bar(
        completeness,
        x="field",
        y="coverage",
        range_y=[0, 100],
        title="Exhaustivité des données",
        template="plotly_white",
    )

    etl_rows = (
        db.session.query(EtlRun)
        .filter(EtlRun.user_id == user_id)
        .order_by(EtlRun.started_at.desc().nullslast())
        .limit(12)
        .all()
    )
    df_etl = pd.DataFrame(
        [
            {
                "run": f"#{r.id}",
                "Extraits": int(r.extracted_count or 0),
                "Transformés": int(r.transformed_count or 0),
                "Chargés": int(r.loaded_count or 0),
            }
            for r in reversed(etl_rows)
        ]
    )
    if df_etl.empty:
        df_etl = pd.DataFrame([{"run": "Aucune donnée", "Extraits": 0, "Transformés": 0, "Chargés": 0}])
    df_etl_long = df_etl.melt(id_vars="run", var_name="step", value_name="count")
    fig_etl = px.line(
        df_etl_long,
        x="run",
        y="count",
        color="step",
        markers=True,
        title="Débit ETL récent",
        template="plotly_white",
    )

    return {
        "top_technologies": _fig_json(fig_top),
        "activity_over_time": _fig_json(fig_time),
        "platform_distribution": _fig_json(fig_platform),
        "location_distribution": _fig_json(fig_loc),
        "profile_growth": _fig_json(fig_growth),
        "followers_repositories": _fig_json(fig_influence),
        "activity_freshness": _fig_json(fig_freshness),
        "data_completeness": _fig_json(fig_completeness),
        "etl_throughput": _fig_json(fig_etl),
    }


def developer_details(developer_id: int, user_id: Optional[int] = None) -> Optional[Dict]:
    dev = db.session.get(Developer, developer_id)
    if not dev:
        return None
    if user_id is not None:
        allowed = UserDeveloper.query.filter_by(user_id=user_id, developer_id=developer_id).first()
        if not allowed:
            return None

    skills = (
        db.session.query(Skill.name, DevSkill.score)
        .join(DevSkill, DevSkill.skill_id == Skill.id)
        .filter(DevSkill.developer_id == developer_id)
        .order_by(DevSkill.score.desc())
        .limit(20)
        .all()
    )

    return {
        "id": dev.id,
        "platform": dev.platform,
        "username": dev.username,
        "display_name": dev.display_name,
        "avatar_url": dev.avatar_url,
        "bio": dev.bio,
        "profile_url": dev.profile_url,
        "location": dev.location,
        "followers_count": dev.followers_count,
        "repos_count": dev.repos_count,
        "last_activity_at": dev.last_activity_at.isoformat() if dev.last_activity_at else None,
        "created_at": dev.created_at.isoformat() if dev.created_at else None,
        "updated_at": dev.updated_at.isoformat() if dev.updated_at else None,
        "contributions_last_year": int(getattr(dev, "contributions_last_year", 0) or 0),
        "skills": [{"name": name, "score": int(score)} for name, score in skills],
    }


def developer_charts(developer_id: int, user_id: Optional[int] = None) -> Dict:
    if user_id is not None:
        allowed = UserDeveloper.query.filter_by(user_id=user_id, developer_id=developer_id).first()
        if not allowed:
            return {"skills_bar": _fig_json(px.bar(pd.DataFrame([{"skill": "Aucune donnée", "score": 0}]), x="skill", y="score", template="plotly_white")), "skills_pie": _fig_json(px.pie(pd.DataFrame([{"skill": "Aucune donnée", "score": 0}]), names="skill", values="score", template="plotly_white"))}
    skills = (
        db.session.query(Skill.name.label("skill"), DevSkill.score.label("score"))
        .join(DevSkill, DevSkill.skill_id == Skill.id)
        .filter(DevSkill.developer_id == developer_id)
        .order_by(DevSkill.score.desc())
        .limit(15)
        .all()
    )
    df = pd.DataFrame(skills, columns=["skill", "score"])
    if df.empty:
        df = pd.DataFrame([{"skill": "Aucune donnée", "score": 0}])

    fig_bar = px.bar(df, x="skill", y="score", title="Répartition technologique", template="plotly_white")
    fig_pie = px.pie(df, names="skill", values="score", title="Répartition des compétences", template="plotly_white")

    return {"skills_bar": _fig_json(fig_bar), "skills_pie": _fig_json(fig_pie)}


def developer_repos(developer_id: int, user_id: Optional[int] = None) -> List[Dict]:
    if user_id is not None:
        allowed = UserDeveloper.query.filter_by(user_id=user_id, developer_id=developer_id).first()
        if not allowed:
            return []
    dev = db.session.get(Developer, developer_id)
    if not dev or not dev.raw_json:
        return []
    try:
        raw = json.loads(dev.raw_json)
    except json.JSONDecodeError:
        return []
    repos = raw.get("repos")
    if not isinstance(repos, list):
        return []
    out: List[Dict] = []
    for r in repos[:15]:
        if not isinstance(r, dict):
            continue
        out.append(
            {
                "name": r.get("name"),
                "html_url": r.get("html_url"),
                "language": r.get("language"),
                "stargazers_count": int(r.get("stargazers_count") or 0),
                "forks_count": int(r.get("forks_count") or 0),
                "pushed_at": r.get("pushed_at"),
            }
        )
    return out
