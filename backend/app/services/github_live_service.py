import json
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple

import requests
from requests import RequestException

from ..extensions import db
from ..models import DevSkill, Developer, Skill


GITHUB_API = "https://api.github.com"


class GitHubRateLimitError(Exception):
    pass


class GitHubLiveSearchError(Exception):
    pass


def _headers(token: str = "") -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "DevScope-Live-Search",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _format_reset_time(reset: Optional[str]) -> str:
    if not reset:
        return ""
    try:
        reset_at = datetime.fromtimestamp(int(reset), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return f"timestamp GitHub {reset}"
    return f"{reset_at.strftime('%Y-%m-%d %H:%M:%S')} UTC"


def _request(url: str, token: str = "", params: Optional[Dict] = None) -> Dict:
    session = requests.Session()
    session.trust_env = False
    try:
        response = session.get(url, headers=_headers(token), params=params, timeout=12)
    except RequestException as exc:
        raise GitHubLiveSearchError(
            "Impossible de joindre GitHub. Vérifiez la connexion réseau, le proxy/VPN et les variables "
            "HTTP_PROXY/HTTPS_PROXY. DevScope ignore maintenant les proxys système pour les appels GitHub."
        ) from exc
    remaining = response.headers.get("X-RateLimit-Remaining")
    message = "GitHub API request failed."
    try:
        message = response.json().get("message", message)
    except ValueError:
        pass

    if response.status_code in (403, 429) and (
        remaining == "0" or "rate limit" in message.lower()
    ):
        reset = response.headers.get("X-RateLimit-Reset")
        detail = "Limite GitHub atteinte."
        if reset:
            detail += f" Reessayez apres {_format_reset_time(reset)}."
        if token:
            detail += " Le GITHUB_TOKEN configure est lui aussi limite pour le moment."
        else:
            detail += " Ajoutez un GITHUB_TOKEN valide dans backend/.env pour augmenter le quota."
        raise GitHubRateLimitError(detail)
    if response.status_code >= 400:
        raise GitHubLiveSearchError(message)
    return response.json()


def _profile_payload(profile: Dict) -> Dict:
    return {
        "id": profile.get("id"),
        "username": profile.get("login", ""),
        "avatar_url": profile.get("avatar_url", ""),
        "bio": profile.get("bio") or "",
        "followers": int(profile.get("followers") or 0),
        "repositories_count": int(profile.get("public_repos") or 0),
        "profile_url": profile.get("html_url", ""),
        "name": profile.get("name") or "",
        "location": profile.get("location") or "",
    }


def _extract_language_skills(repos: List[Dict]) -> List[Tuple[str, int]]:
    counts: Dict[str, int] = {}
    for repo in repos:
        language = repo.get("language")
        if language:
            counts[language] = counts.get(language, 0) + 1
    return sorted(counts.items(), key=lambda item: item[1], reverse=True)[:20]


def _replace_skills(developer_id: int, skills: List[Tuple[str, int]]) -> None:
    if not skills:
        return
    DevSkill.query.filter_by(developer_id=developer_id).delete()
    for name, score in skills:
        skill = Skill.query.filter(db.func.lower(Skill.name) == name.lower()).first()
        if not skill:
            skill = Skill(name=name)
            db.session.add(skill)
            db.session.flush()
        db.session.add(DevSkill(developer_id=developer_id, skill_id=skill.id, score=int(score), source="github_live"))


def search_github_users(username: str, token: str = "", limit: int = 5) -> List[Dict]:
    username = (username or "").strip()
    if not username:
        return []

    limit = max(1, min(10, int(limit or 5)))
    search = _request(
        f"{GITHUB_API}/search/users",
        token=token,
        params={"q": f"{username} in:login type:user", "per_page": limit},
    )

    users = []
    for item in (search.get("items") or [])[:limit]:
        login = item.get("login")
        if not login:
            continue
        profile = _request(f"{GITHUB_API}/users/{login}", token=token)
        users.append(_profile_payload(profile))
    return users


def save_github_profile(username: str, token: str = "") -> Tuple[Developer, bool]:
    username = (username or "").strip()
    if not username:
        raise GitHubLiveSearchError("Username is required.")

    profile = _request(f"{GITHUB_API}/users/{username}", token=token)
    repos = _request(
        f"{GITHUB_API}/users/{username}/repos",
        token=token,
        params={"per_page": 30, "sort": "pushed"},
    )
    if not isinstance(repos, list):
        repos = []
    existing = Developer.query.filter_by(platform="github", username=profile.get("login")).first()
    created = existing is None
    developer = existing or Developer(platform="github", username=profile.get("login"))

    developer.display_name = profile.get("name") or profile.get("login")
    developer.avatar_url = profile.get("avatar_url")
    developer.bio = profile.get("bio")
    developer.profile_url = profile.get("html_url")
    developer.location = profile.get("location")
    developer.followers_count = int(profile.get("followers") or 0)
    developer.repos_count = int(profile.get("public_repos") or 0)
    developer.last_activity_at = None
    for repo in repos:
        pushed_at = repo.get("pushed_at")
        if not pushed_at:
            continue
        try:
            dt = datetime.fromisoformat(pushed_at.replace("Z", "+00:00")).replace(tzinfo=None)
        except ValueError:
            continue
        if not developer.last_activity_at or dt > developer.last_activity_at:
            developer.last_activity_at = dt
    developer.updated_at = datetime.utcnow()
    developer.raw_json = json.dumps(profile)

    if created:
        db.session.add(developer)
        db.session.flush()
    _replace_skills(developer.id, _extract_language_skills(repos))
    db.session.commit()
    return developer, created
