import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import requests
from bs4 import BeautifulSoup
from requests import RequestException


class GitHubCollectorError(Exception):
    pass


class GitHubRateLimitError(GitHubCollectorError):
    pass


def _headers(token: str) -> Dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "DevScope-ETL",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _github_get(url: str, token: str = "", params: Optional[Dict[str, Any]] = None, timeout: int = 20):
    session = requests.Session()
    session.trust_env = False
    try:
        resp = session.get(url, headers=_headers(token), params=params, timeout=timeout)
    except RequestException as exc:
        raise GitHubCollectorError(
            "Impossible de joindre GitHub. Vérifiez la connexion réseau, le proxy/VPN et les variables "
            "HTTP_PROXY/HTTPS_PROXY. DevScope ignore maintenant les proxys système pour les appels GitHub."
        ) from exc
    return resp


def _format_reset_time(reset: Optional[str]) -> str:
    if not reset:
        return ""
    try:
        reset_at = datetime.fromtimestamp(int(reset), tz=timezone.utc)
    except (TypeError, ValueError, OSError):
        return f"timestamp GitHub {reset}"
    return f"{reset_at.strftime('%Y-%m-%d %H:%M:%S')} UTC"


def _raise_for_github_error(resp, token: str = "") -> None:
    if resp.status_code < 400:
        return

    remaining = resp.headers.get("X-RateLimit-Remaining")
    reset = resp.headers.get("X-RateLimit-Reset")
    message = ""
    try:
        message = (resp.json() or {}).get("message", "")
    except ValueError:
        message = resp.text or ""

    if resp.status_code in (403, 429) and (
        remaining == "0" or "rate limit" in message.lower()
    ):
        detail = "Limite GitHub atteinte."
        if reset:
            detail += f" Reessayez apres {_format_reset_time(reset)}."
        if token:
            detail += " Le GITHUB_TOKEN configure est lui aussi limite pour le moment."
        else:
            detail += " Ajoutez un GITHUB_TOKEN valide dans backend/.env pour augmenter le quota."
        raise GitHubRateLimitError(detail)

    resp.raise_for_status()


def _public_get(url: str, timeout: int = 20, headers: Optional[Dict[str, str]] = None):
    session = requests.Session()
    session.trust_env = False
    try:
        return session.get(url, timeout=timeout, headers=headers)
    except RequestException as exc:
        raise GitHubCollectorError(
            "Impossible de joindre github.com pour lire les contributions. Vérifiez la connexion réseau."
        ) from exc


def search_users(query: str, token: str, limit: int = 25) -> List[str]:
    usernames: List[str] = []
    page = 1
    per_page = 100
    seen = set()

    while len(usernames) < limit:
        url = "https://api.github.com/search/users"
        params = {"q": query, "per_page": min(per_page, limit - len(usernames)), "page": page}
        resp = _github_get(url, token=token, params=params, timeout=20)
        _raise_for_github_error(resp, token=token)
        data = resp.json()
        items = data.get("items", [])
        if not items:
            break
        for item in items:
            login = item.get("login")
            if not login or login in seen:
                continue
            seen.add(login)
            usernames.append(login)
            if len(usernames) >= limit:
                break
        page += 1

        if page > 10:
            break

    return usernames[:limit]


def fetch_user(username: str, token: str) -> Dict[str, Any]:
    url = f"https://api.github.com/users/{username}"
    resp = _github_get(url, token=token, timeout=20)
    _raise_for_github_error(resp, token=token)
    return resp.json()


def fetch_repos(username: str, token: str, max_repos: int = 30) -> List[Dict[str, Any]]:
    url = f"https://api.github.com/users/{username}/repos"
    params = {"per_page": min(100, max_repos), "sort": "pushed"}
    resp = _github_get(url, token=token, params=params, timeout=20)
    _raise_for_github_error(resp, token=token)
    data = resp.json()
    if not isinstance(data, list):
        return []
    return data[:max_repos]


def parse_iso_datetime(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def simplify_repos(repos: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for r in repos[:limit]:
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


def scrape_contributions_last_year(username: str) -> Optional[int]:
    url = f"https://github.com/{username}"
    resp = _public_get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
    if resp.status_code != 200:
        return None
    soup = BeautifulSoup(resp.text, "html.parser")
    text = soup.get_text(" ", strip=True)
    m = re.search(r"([\d,]+)\s+contributions?\s+in the last year", text, re.IGNORECASE)
    if not m:
        return None
    return int(m.group(1).replace(",", ""))


def extract_language_skills(repos: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
    counts: Dict[str, int] = {}
    for r in repos:
        lang = r.get("language")
        if not lang:
            continue
        counts[lang] = counts.get(lang, 0) + 1
    skills = sorted(counts.items(), key=lambda x: x[1], reverse=True)
    return skills[:20]


def last_repo_activity(repos: List[Dict[str, Any]]) -> Optional[datetime]:
    best: Optional[datetime] = None
    for r in repos:
        pushed_at = r.get("pushed_at")
        if not pushed_at:
            continue
        dt = parse_iso_datetime(pushed_at)
        if not dt:
            continue
        if not best or dt > best:
            best = dt
    return best
