from datetime import datetime, timedelta
from typing import Dict, List, Optional

from sqlalchemy import and_, func, or_

from ..models import DevSkill, Developer, Skill, UserDeveloper
from .profile_management_service import developer_payload


def _activity_level(last_activity_at: Optional[datetime]) -> str:
    if not last_activity_at:
        return "low"
    days = (datetime.utcnow() - last_activity_at).days
    if days <= 30:
        return "high"
    if days <= 90:
        return "medium"
    return "low"


def _split_csv(value: str) -> List[str]:
    parts = [p.strip() for p in (value or "").split(",")]
    return [p for p in parts if p]


def search_developers(
    user_id: Optional[int] = None,
    q: str = "",
    technologies: str = "",
    platform: str = "",
    activity: str = "",
    recent_days: Optional[int] = None,
    min_repos: Optional[int] = None,
    max_repos: Optional[int] = None,
    min_followers: Optional[int] = None,
    max_followers: Optional[int] = None,
    location: str = "",
    sort: str = "activity",
    order: str = "desc",
    limit: int = 50,
) -> List[Dict]:
    q = q.strip()
    technologies_list = _split_csv(technologies)
    platform = platform.strip()
    activity = activity.strip().lower()
    location = location.strip()
    sort = (sort or "activity").strip().lower()
    order = (order or "desc").strip().lower()

    query = Developer.query
    if user_id is not None:
        query = query.join(UserDeveloper, UserDeveloper.developer_id == Developer.id).filter(
            UserDeveloper.user_id == user_id
        )

    filters = []
    if q:
        like = f"%{q.lower()}%"
        filters.append(
            or_(
                func.lower(Developer.username).like(like),
                func.lower(Developer.display_name).like(like),
                func.lower(Developer.location).like(like),
            )
        )

    if platform:
        filters.append(func.lower(Developer.platform) == platform.lower())

    if location:
        like = f"%{location.lower()}%"
        filters.append(func.lower(Developer.location).like(like))

    if recent_days is not None:
        since = datetime.utcnow() - timedelta(days=recent_days)
        filters.append(Developer.last_activity_at.isnot(None))
        filters.append(Developer.last_activity_at >= since)

    if min_repos is not None:
        filters.append(Developer.repos_count >= int(min_repos))
    if max_repos is not None:
        filters.append(Developer.repos_count <= int(max_repos))

    if min_followers is not None:
        filters.append(Developer.followers_count >= int(min_followers))
    if max_followers is not None:
        filters.append(Developer.followers_count <= int(max_followers))

    if filters:
        query = query.filter(and_(*filters))

    if technologies_list:
        query = (
            query.join(DevSkill, DevSkill.developer_id == Developer.id)
            .join(Skill, Skill.id == DevSkill.skill_id)
            .filter(func.lower(Skill.name).in_([t.lower() for t in technologies_list]))
        )

    query = query.distinct()

    sort_map = {
        "activity": Developer.last_activity_at,
        "followers": Developer.followers_count,
        "repos": Developer.repos_count,
        "name": Developer.username,
        "updated": Developer.updated_at,
        "created": Developer.updated_at,
    }
    score_expr = (
        Developer.followers_count * 0.30
        + Developer.repos_count * 3.0
        + Developer.contributions_last_year * 0.15
    )
    col = score_expr if sort == "score" else sort_map.get(sort, Developer.last_activity_at)
    desc = order != "asc"

    if sort == "score":
        query = query.order_by(col.desc() if desc else col.asc(), Developer.updated_at.desc())
    elif col is Developer.last_activity_at:
        query = query.order_by(col.desc().nullslast() if desc else col.asc().nullslast(), Developer.repos_count.desc())
    else:
        query = query.order_by(col.desc() if desc else col.asc(), Developer.last_activity_at.desc().nullslast())

    results = []
    for dev in query.limit(limit).all():
        level = _activity_level(dev.last_activity_at)
        if activity and level != activity:
            continue
        results.append(developer_payload(dev, user_id=user_id))

    return results


def search_developers_paginated(
    user_id: Optional[int] = None,
    q: str = "",
    technologies: str = "",
    platform: str = "",
    activity: str = "",
    recent_days: Optional[int] = None,
    min_repos: Optional[int] = None,
    max_repos: Optional[int] = None,
    min_followers: Optional[int] = None,
    max_followers: Optional[int] = None,
    location: str = "",
    sort: str = "activity",
    order: str = "desc",
    page: int = 1,
    per_page: int = 18,
) -> Dict:
    """Search developers with server-side pagination and total count.

    Returns a dict shaped as: {"items": [...], "total": int, "page": int, "per_page": int}.
    """
    q = q.strip()
    technologies_list = _split_csv(technologies)
    platform = platform.strip()
    activity = activity.strip().lower()
    location = location.strip()
    sort = (sort or "activity").strip().lower()
    order = (order or "desc").strip().lower()

    page = max(1, int(page or 1))
    per_page = max(1, min(60, int(per_page or 18)))

    query = Developer.query
    if user_id is not None:
        query = query.join(UserDeveloper, UserDeveloper.developer_id == Developer.id).filter(
            UserDeveloper.user_id == user_id
        )

    filters = []
    if q:
        like = f"%{q.lower()}%"
        filters.append(
            or_(
                func.lower(Developer.username).like(like),
                func.lower(Developer.display_name).like(like),
                func.lower(Developer.location).like(like),
            )
        )

    if platform:
        filters.append(func.lower(Developer.platform) == platform.lower())

    if location:
        like = f"%{location.lower()}%"
        filters.append(func.lower(Developer.location).like(like))

    if recent_days is not None:
        since = datetime.utcnow() - timedelta(days=recent_days)
        filters.append(Developer.last_activity_at.isnot(None))
        filters.append(Developer.last_activity_at >= since)

    if min_repos is not None:
        filters.append(Developer.repos_count >= int(min_repos))
    if max_repos is not None:
        filters.append(Developer.repos_count <= int(max_repos))

    if min_followers is not None:
        filters.append(Developer.followers_count >= int(min_followers))
    if max_followers is not None:
        filters.append(Developer.followers_count <= int(max_followers))

    if activity:
        now = datetime.utcnow()
        if activity == "high":
            filters.append(Developer.last_activity_at.isnot(None))
            filters.append(Developer.last_activity_at >= now - timedelta(days=30))
        elif activity == "medium":
            filters.append(Developer.last_activity_at.isnot(None))
            filters.append(Developer.last_activity_at < now - timedelta(days=30))
            filters.append(Developer.last_activity_at >= now - timedelta(days=90))
        elif activity == "low":
            filters.append(
                or_(
                    Developer.last_activity_at.is_(None),
                    Developer.last_activity_at < now - timedelta(days=90),
                )
            )

    if filters:
        query = query.filter(and_(*filters))

    if technologies_list:
        query = (
            query.join(DevSkill, DevSkill.developer_id == Developer.id)
            .join(Skill, Skill.id == DevSkill.skill_id)
            .filter(func.lower(Skill.name).in_([t.lower() for t in technologies_list]))
        )

    query = query.distinct()

    sort_map = {
        "activity": Developer.last_activity_at,
        "followers": Developer.followers_count,
        "repos": Developer.repos_count,
        "name": Developer.username,
        "updated": Developer.updated_at,
        "created": Developer.updated_at,
    }
    score_expr = (
        Developer.followers_count * 0.30
        + Developer.repos_count * 3.0
        + Developer.contributions_last_year * 0.15
    )
    col = score_expr if sort == "score" else sort_map.get(sort, Developer.last_activity_at)
    desc = order != "asc"

    if sort == "score":
        query = query.order_by(col.desc() if desc else col.asc(), Developer.updated_at.desc())
    elif col is Developer.last_activity_at:
        query = query.order_by(
            col.desc().nullslast() if desc else col.asc().nullslast(),
            Developer.repos_count.desc(),
        )
    else:
        query = query.order_by(
            col.desc() if desc else col.asc(),
            Developer.last_activity_at.desc().nullslast(),
        )

    total = query.with_entities(Developer.id).distinct().count()
    rows = (
        query.offset((page - 1) * per_page)
        .limit(per_page)
        .all()
    )

    items: List[Dict] = [developer_payload(dev, user_id=user_id) for dev in rows]
    return {"items": items, "total": total, "page": page, "per_page": per_page}
