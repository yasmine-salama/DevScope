import json
from datetime import datetime
from typing import Dict, List, Optional

import pandas as pd

from ..extensions import db
from ..models import DevSkill, Developer, EtlLog, EtlRun, Skill
from ..services.user_data_service import link_developer_to_user
from .github_collector import (
    GitHubRateLimitError,
    extract_language_skills,
    fetch_repos,
    fetch_user,
    last_repo_activity,
    parse_iso_datetime,
    scrape_contributions_last_year,
    search_users,
    simplify_repos,
)


def _log(run_id: int, level: str, message: str) -> None:
    db.session.add(EtlLog(etl_run_id=run_id, level=level, message=message))
    db.session.commit()


def _get_or_create_skill(name: str) -> Skill:
    s = Skill.query.filter_by(name=name).first()
    if s:
        return s
    s = Skill(name=name)
    db.session.add(s)
    db.session.commit()
    return s


def run_etl_github(query: str, token: str, limit: int = 25, user_id: Optional[int] = None) -> Dict:
    run = EtlRun(user_id=user_id, source="github", query=query, status="running", started_at=datetime.utcnow())
    db.session.add(run)
    db.session.commit()

    extracted: List[Dict] = []
    try:
        candidate_limit = min(1000, max(limit * 5, limit + 20))
        usernames = search_users(query=query, token=token, limit=candidate_limit)
        _log(run.id, "info", f"Found {len(usernames)} GitHub candidate users for query.")

        for username in usernames:
            if len(extracted) >= limit:
                break
            try:
                user = fetch_user(username=username, token=token)
                repos = fetch_repos(username=username, token=token, max_repos=30)
                try:
                    contributions = scrape_contributions_last_year(username=username)
                except Exception as exc:
                    contributions = None
                    _log(run.id, "warning", f"Contributions ignored for {username}: {exc}")

                skills = extract_language_skills(repos)
                last_activity_at = last_repo_activity(repos)
                created_at = parse_iso_datetime(user.get("created_at"))
                repos_snapshot = simplify_repos(repos, limit=10)

                if contributions is None:
                    _log(run.id, "warning", f"Could not read contributions for {username}.")

                extracted.append(
                    {
                        "platform": "github",
                        "username": user.get("login") or username,
                        "display_name": user.get("name") or user.get("login") or username,
                        "avatar_url": user.get("avatar_url"),
                        "bio": user.get("bio"),
                        "profile_url": user.get("html_url") or f"https://github.com/{username}",
                        "location": user.get("location"),
                        "followers_count": int(user.get("followers") or 0),
                        "repos_count": int(user.get("public_repos") or 0),
                        "last_activity_at": last_activity_at,
                        "created_at": created_at,
                        "contributions_last_year": contributions,
                        "skills": skills,
                        "repos_snapshot": repos_snapshot,
                        "raw_user": user,
                    }
                )
            except GitHubRateLimitError as e:
                _log(run.id, "warning", f"GitHub rate limit reached. ETL stopped after {len(extracted)} valid profiles. {e}")
                break
            except Exception as e:
                _log(run.id, "error", f"{username}: {e}")
                continue

        if len(extracted) < limit:
            _log(run.id, "warning", f"Collected {len(extracted)} valid profiles out of requested {limit}. GitHub candidates were exhausted or invalid.")

        run.extracted_count = len(extracted)
        db.session.commit()

        df = pd.DataFrame(extracted)
        duplicates_removed = 0
        missing_values_filled = 0
        if not df.empty:
            before = len(df)
            df = df.drop_duplicates(subset=["platform", "username"])
            duplicates_removed = before - len(df)
            missing_values_filled = int(df["location"].isna().sum()) if "location" in df.columns else 0
            df["location"] = df["location"].fillna("")
        transformed = df.to_dict(orient="records")

        run.transformed_count = len(transformed)
        run.duplicates_removed = int(duplicates_removed)
        run.missing_values_filled = int(missing_values_filled)
        db.session.commit()

        loaded = 0
        created = 0
        updated = 0
        linked = 0
        for row in transformed:
            platform = row["platform"]
            username = row["username"]
            dev = Developer.query.filter_by(platform=platform, username=username).first()
            if not dev:
                dev = Developer(platform=platform, username=username, profile_url=row["profile_url"])
                db.session.add(dev)
                created += 1
            else:
                updated += 1

            dev.display_name = row.get("display_name")
            dev.avatar_url = row.get("avatar_url")
            dev.bio = row.get("bio")
            dev.profile_url = row.get("profile_url")
            dev.location = row.get("location")
            dev.followers_count = int(row.get("followers_count") or 0)
            dev.repos_count = int(row.get("repos_count") or 0)
            dev.last_activity_at = row.get("last_activity_at")
            if not dev.created_at:
                dev.created_at = row.get("created_at")
            dev.updated_at = datetime.utcnow()
            dev.contributions_last_year = int(row.get("contributions_last_year") or 0)
            dev.raw_json = json.dumps(
                {
                    "contributions_last_year": row.get("contributions_last_year"),
                    "repos": row.get("repos_snapshot", []),
                    "raw_user": row.get("raw_user", {}),
                },
                ensure_ascii=False,
            )
            db.session.flush()
            if link_developer_to_user(user_id, dev.id, source="etl"):
                linked += 1

            skills = row.get("skills") or []
            current_skill_names = {name for name, _score in skills}
            stale_links = (
                DevSkill.query.join(Skill, Skill.id == DevSkill.skill_id)
                .filter(DevSkill.developer_id == dev.id, DevSkill.source == "github")
                .all()
            )
            for link in stale_links:
                if link.skill.name not in current_skill_names:
                    db.session.delete(link)
            for skill_name, score in skills:
                s = _get_or_create_skill(skill_name)
                link = DevSkill.query.filter_by(developer_id=dev.id, skill_id=s.id).first()
                if not link:
                    link = DevSkill(developer_id=dev.id, skill_id=s.id, score=int(score), source="github")
                    db.session.add(link)
                else:
                    link.score = int(score)
                    link.source = "github"

            loaded += 1

        db.session.commit()

        run.loaded_count = loaded
        run.created_count = created
        run.updated_count = updated
        run.linked_count = linked
        run.status = "success"
        run.finished_at = datetime.utcnow()
        run.error_count = (
            db.session.query(db.func.count(EtlLog.id))
            .filter(EtlLog.etl_run_id == run.id, EtlLog.level == "error")
            .scalar()
            or 0
        )
        db.session.commit()

        _log(run.id, "info", f"Loaded {loaded} developer profiles: {created} created, {updated} updated, {linked} linked to user.")
        return {
            "etl_run_id": run.id,
            "status": run.status,
            "loaded_count": loaded,
            "created_count": created,
            "updated_count": updated,
            "linked_count": linked,
        }
    except Exception as e:
        run.status = "failed"
        run.finished_at = datetime.utcnow()
        run.error_count = int(getattr(run, "error_count", 0) or 0) + 1
        db.session.commit()
        _log(run.id, "error", str(e))
        raise


def recent_etl_runs(limit: int = 20, user_id: Optional[int] = None) -> List[Dict]:
    query = db.session.query(EtlRun)
    if user_id is not None:
        query = query.filter(EtlRun.user_id == user_id)
    runs = query.order_by(EtlRun.started_at.desc()).limit(limit).all()
    return [
        {
            "id": r.id,
            "source": r.source,
            "query": r.query,
            "status": r.status,
            "extracted_count": r.extracted_count,
            "transformed_count": r.transformed_count,
            "loaded_count": r.loaded_count,
            "created_count": int(getattr(r, "created_count", 0) or 0),
            "updated_count": int(getattr(r, "updated_count", 0) or 0),
            "linked_count": int(getattr(r, "linked_count", 0) or 0),
            "duplicates_removed": int(getattr(r, "duplicates_removed", 0) or 0),
            "missing_values_filled": int(getattr(r, "missing_values_filled", 0) or 0),
            "error_count": int(getattr(r, "error_count", 0) or 0),
            "started_at": r.started_at.isoformat() if r.started_at else None,
            "finished_at": r.finished_at.isoformat() if r.finished_at else None,
        }
        for r in runs
    ]


def etl_run_logs(etl_run_id: int, limit: int = 30) -> List[Dict]:
    logs = (
        EtlLog.query.filter_by(etl_run_id=etl_run_id)
        .order_by(EtlLog.created_at.desc())
        .limit(limit)
        .all()
    )
    return [
        {"level": l.level, "message": l.message, "created_at": l.created_at.isoformat()}
        for l in logs
    ]
