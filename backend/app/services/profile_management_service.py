from datetime import datetime
from typing import Dict, List, Optional, Tuple

from ..extensions import db
from ..models import DevSkill, Developer, Favorite, ProfileOperation, Skill, UserDeveloper
from .user_data_service import user_can_access_developer


def _activity_level(last_activity_at: Optional[datetime]) -> str:
    if not last_activity_at:
        return "low"
    days = (datetime.utcnow() - last_activity_at).days
    if days <= 30:
        return "high"
    if days <= 90:
        return "medium"
    return "low"


def _global_score(dev: Developer, skills_count: int = 0) -> float:
    followers = min(float(dev.followers_count or 0) / 1000.0, 1.0)
    repos = min(float(dev.repos_count or 0) / 100.0, 1.0)
    contributions = min(float(getattr(dev, "contributions_last_year", 0) or 0) / 1000.0, 1.0)
    skill_score = min(float(skills_count or 0) / 10.0, 1.0)
    activity = 0.0
    if dev.last_activity_at:
        days = max(0, (datetime.utcnow() - dev.last_activity_at).days)
        activity = max(0.0, 1.0 - min(days, 365) / 365.0)
    return round((0.30 * followers + 0.25 * repos + 0.20 * activity + 0.15 * contributions + 0.10 * skill_score) * 100, 1)


def skills_for_developer(developer_id: int) -> List[Dict]:
    rows = (
        db.session.query(Skill.name, DevSkill.score, DevSkill.source)
        .join(DevSkill, DevSkill.skill_id == Skill.id)
        .filter(DevSkill.developer_id == developer_id)
        .order_by(DevSkill.score.desc(), Skill.name.asc())
        .all()
    )
    return [{"name": name, "score": int(score or 0), "source": source} for name, score, source in rows]


def developer_payload(dev: Developer, user_id: Optional[int] = None, include_raw: bool = False) -> Dict:
    skills = skills_for_developer(dev.id)
    payload = {
        "id": dev.id,
        "platform": dev.platform,
        "username": dev.username,
        "display_name": dev.display_name or dev.username,
        "avatar_url": dev.avatar_url,
        "bio": dev.bio or "",
        "profile_url": dev.profile_url,
        "location": dev.location or "",
        "followers_count": int(dev.followers_count or 0),
        "repos_count": int(dev.repos_count or 0),
        "last_activity_at": dev.last_activity_at.isoformat() if dev.last_activity_at else None,
        "created_at": dev.created_at.isoformat() if dev.created_at else None,
        "updated_at": dev.updated_at.isoformat() if dev.updated_at else None,
        "contributions_last_year": int(getattr(dev, "contributions_last_year", 0) or 0),
        "activity_level": _activity_level(dev.last_activity_at),
        "skills": skills,
        "technologies": [s["name"] for s in skills],
        "global_score": _global_score(dev, len(skills)),
        "status": "Deja enregistre",
        "can_manage": bool(user_id and user_can_access_developer(user_id, dev.id)),
    }
    if include_raw:
        payload["raw_json"] = dev.raw_json
    return payload


def log_profile_operation(
    user_id: int,
    operation: str,
    developer: Optional[Developer] = None,
    username: str = "",
    platform: str = "github",
    message: str = "",
) -> ProfileOperation:
    op = ProfileOperation(
        user_id=user_id,
        developer_id=developer.id if developer else None,
        username=(developer.username if developer else username) or "",
        platform=(developer.platform if developer else platform) or "github",
        operation=operation,
        message=message or "",
    )
    db.session.add(op)
    return op


def parse_skills(payload: object) -> List[Tuple[str, int]]:
    if isinstance(payload, str):
        values = [p.strip() for p in payload.split(",") if p.strip()]
        return [(name, 1) for name in values]
    if not isinstance(payload, list):
        return []
    parsed: List[Tuple[str, int]] = []
    for item in payload:
        if isinstance(item, str):
            name = item.strip()
            score = 1
        elif isinstance(item, dict):
            name = str(item.get("name") or "").strip()
            try:
                score = int(item.get("score") or 1)
            except (TypeError, ValueError):
                score = 1
        else:
            continue
        if name:
            parsed.append((name[:100], max(0, min(100, score))))
    return parsed


def replace_developer_skills(developer_id: int, skills: List[Tuple[str, int]], source: str = "manual") -> None:
    DevSkill.query.filter_by(developer_id=developer_id).delete()
    seen = set()
    for name, score in skills:
        key = name.lower()
        if key in seen:
            continue
        seen.add(key)
        skill = Skill.query.filter(db.func.lower(Skill.name) == key).first()
        if not skill:
            skill = Skill(name=name)
            db.session.add(skill)
            db.session.flush()
        db.session.add(DevSkill(developer_id=developer_id, skill_id=skill.id, score=score, source=source))


def update_developer_profile(user_id: int, developer_id: int, payload: Dict) -> Dict:
    dev = db.session.get(Developer, developer_id)
    if not dev or not user_can_access_developer(user_id, developer_id):
        raise PermissionError("Profil introuvable ou permission insuffisante.")

    dev.display_name = str(payload.get("display_name") or dev.username).strip()[:150]
    dev.bio = str(payload.get("bio") or "").strip()
    dev.location = str(payload.get("location") or "").strip()[:150]
    dev.profile_url = str(payload.get("profile_url") or dev.profile_url).strip()
    dev.avatar_url = str(payload.get("avatar_url") or "").strip()
    dev.platform = str(payload.get("platform") or dev.platform).strip().lower()[:30]
    try:
        dev.followers_count = max(0, int(payload.get("followers_count") or 0))
        dev.repos_count = max(0, int(payload.get("repos_count") or 0))
        dev.contributions_last_year = max(0, int(payload.get("contributions_last_year") or 0))
    except (TypeError, ValueError) as exc:
        raise ValueError("Followers, repositories et contributions doivent etre numeriques.") from exc

    skills = parse_skills(payload.get("skills"))
    replace_developer_skills(dev.id, skills, source="manual")
    dev.updated_at = datetime.utcnow()
    log_profile_operation(user_id, "update", dev, message="Profil modifie depuis Search.")
    db.session.commit()
    return developer_payload(dev, user_id=user_id)


def delete_developer_profile(user_id: int, developer_id: int) -> Dict:
    dev = db.session.get(Developer, developer_id)
    if not dev or not user_can_access_developer(user_id, developer_id):
        raise PermissionError("Profil introuvable ou permission insuffisante.")

    username = dev.username
    platform = dev.platform
    Favorite.query.filter_by(developer_id=developer_id).delete()
    UserDeveloper.query.filter_by(developer_id=developer_id).delete()
    DevSkill.query.filter_by(developer_id=developer_id).delete()
    log_profile_operation(user_id, "delete", dev, message="Profil supprime depuis Search.")
    db.session.flush()
    db.session.delete(dev)
    db.session.commit()
    return {"deleted": True, "username": username, "platform": platform}


def recent_profile_operations(user_id: int, limit: int = 20) -> List[Dict]:
    rows = (
        ProfileOperation.query.filter_by(user_id=user_id)
        .order_by(ProfileOperation.created_at.desc())
        .limit(max(1, min(100, int(limit or 20))))
        .all()
    )
    return [
        {
            "id": row.id,
            "developer_id": row.developer_id,
            "username": row.username,
            "platform": row.platform,
            "operation": row.operation,
            "message": row.message,
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }
        for row in rows
    ]

