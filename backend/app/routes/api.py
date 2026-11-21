import io
from typing import Optional

from flask import Blueprint, current_app, jsonify, request, send_file, session

from ..etl.pipeline import etl_run_logs, recent_etl_runs, run_etl_github
from ..services.analytics_service import (
    dashboard_charts,
    dashboard_summary,
    developer_charts,
    developer_details,
    developer_repos,
)
from ..services.api_utils import err, ok
from ..services.export_service import (
    export_dashboard_pdf,
    export_developer_pdf,
    export_table_csv,
    export_table_xlsx,
)
from ..services.github_live_service import (
    GitHubLiveSearchError,
    GitHubRateLimitError,
    save_github_profile,
    search_github_users,
)
from ..services.profile_management_service import (
    delete_developer_profile,
    developer_payload,
    log_profile_operation,
    recent_profile_operations,
    update_developer_profile,
)
from ..services.search_service import search_developers, search_developers_paginated
from ..extensions import db
from ..models import Developer, DevSkill, EtlLog, EtlRun, Favorite, Skill
from ..models import SearchHistory, UserDeveloper
from ..services.auth_service import require_login
from ..services.user_data_service import link_developer_to_user, user_can_access_developer

bp = Blueprint("api", __name__, url_prefix="/api")


def _user_id() -> Optional[int]:
    uid = session.get("user_id")
    return int(uid) if uid else None


@bp.get("/dashboard/summary")
@require_login
def dashboard_summary_api():
    return jsonify(ok(dashboard_summary(_user_id())))


@bp.get("/dashboard/charts")
@require_login
def dashboard_charts_api():
    return jsonify(ok(dashboard_charts(_user_id())))


@bp.get("/search")
@require_login
def search_api():
    q = request.args.get("q", "")
    technologies = request.args.get("technologies", "") or request.args.get("technology", "")
    platform = request.args.get("platform", "")
    activity = request.args.get("activity", "")
    location = request.args.get("location", "")
    recent_days_raw = request.args.get("recent_days")
    limit_raw = request.args.get("limit", "50")
    page_raw = request.args.get("page")
    per_page_raw = request.args.get("per_page")
    min_repos_raw = request.args.get("min_repos")
    max_repos_raw = request.args.get("max_repos")
    min_followers_raw = request.args.get("min_followers")
    max_followers_raw = request.args.get("max_followers")
    sort = request.args.get("sort", "activity")
    order = request.args.get("order", "desc")

    recent_days = int(recent_days_raw) if recent_days_raw else None
    limit = max(1, min(200, int(limit_raw)))
    page = int(page_raw) if page_raw else None
    per_page = int(per_page_raw) if per_page_raw else None
    min_repos = int(min_repos_raw) if min_repos_raw else None
    max_repos = int(max_repos_raw) if max_repos_raw else None
    min_followers = int(min_followers_raw) if min_followers_raw else None
    max_followers = int(max_followers_raw) if max_followers_raw else None

    entry = {
        "q": q,
        "technologies": technologies,
        "platform": platform,
        "activity": activity,
        "location": location,
        "recent_days": recent_days,
        "min_repos": min_repos,
        "max_repos": max_repos,
        "min_followers": min_followers,
        "max_followers": max_followers,
        "sort": sort,
        "order": order,
    }
    uid = _user_id()
    last = (
        SearchHistory.query.filter_by(user_id=uid)
        .order_by(SearchHistory.created_at.desc())
        .first()
    )
    comparable = {k: getattr(last, k) for k in entry.keys()} if last else None
    if comparable != entry:
        db.session.add(SearchHistory(user_id=uid, **entry))
        db.session.commit()

    if page is not None or per_page is not None:
        res = search_developers_paginated(
            user_id=uid,
            q=q,
            technologies=technologies,
            platform=platform,
            activity=activity,
            recent_days=recent_days,
            min_repos=min_repos,
            max_repos=max_repos,
            min_followers=min_followers,
            max_followers=max_followers,
            location=location,
            sort=sort,
            order=order,
            page=page or 1,
            per_page=per_page or 18,
        )
        return jsonify(ok(res))

    items = search_developers(
        user_id=uid,
        q=q,
        technologies=technologies,
        platform=platform,
        activity=activity,
        recent_days=recent_days,
        min_repos=min_repos,
        max_repos=max_repos,
        min_followers=min_followers,
        max_followers=max_followers,
        location=location,
        sort=sort,
        order=order,
        limit=limit,
    )
    return jsonify(ok({"items": items, "total": len(items), "page": 1, "per_page": limit}))


@bp.get("/search/history")
@require_login
def search_history_api():
    uid = _user_id()
    rows = (
        SearchHistory.query.filter_by(user_id=uid)
        .order_by(SearchHistory.created_at.desc())
        .limit(10)
        .all()
    )
    items = [
        {
            "q": r.q or "",
            "technologies": r.technologies or "",
            "platform": r.platform or "",
            "activity": r.activity or "",
            "location": r.location or "",
            "recent_days": r.recent_days,
            "min_repos": r.min_repos,
            "max_repos": r.max_repos,
            "min_followers": r.min_followers,
            "max_followers": r.max_followers,
            "sort": r.sort or "activity",
            "order": r.order or "desc",
        }
        for r in rows
    ]
    return jsonify(ok({"items": items}))


@bp.get("/github/users")
@require_login
def github_users_api():
    q = (request.args.get("q") or "").strip()
    try:
        limit = max(1, min(10, int(request.args.get("limit") or 5)))
    except ValueError:
        limit = 5
    if not q:
        return jsonify(ok({"items": [], "total": 0, "limit": limit}))

    try:
        token = current_app.config.get("GITHUB_TOKEN", "")
        items = search_github_users(q, token=token, limit=limit)
        for item in items:
            existing = Developer.query.filter_by(platform="github", username=item.get("username")).first()
            linked = (
                UserDeveloper.query.filter_by(user_id=_user_id(), developer_id=existing.id).first()
                if existing
                else None
            )
            item["exists_in_database"] = existing is not None
            item["developer_id"] = existing.id if existing else None
            item["status"] = "Deja enregistre" if linked else ("Existe dans la base" if existing else "Nouveau profil GitHub")
        return jsonify(ok({"items": items, "total": len(items), "limit": limit}))
    except GitHubRateLimitError as e:
        return jsonify(err(str(e), "github_rate_limit")), 429
    except GitHubLiveSearchError as e:
        return jsonify(err(str(e), "github_api_error")), 502


@bp.post("/github/users/save")
@require_login
def github_user_save_api():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    if not username:
        return jsonify(err("Le nom d'utilisateur est obligatoire.", "validation_error")), 400
    try:
        token = current_app.config.get("GITHUB_TOKEN", "")
        existing = Developer.query.filter_by(platform="github", username=username).first()
        if existing and UserDeveloper.query.filter_by(user_id=_user_id(), developer_id=existing.id).first():
            log_profile_operation(
                _user_id(),
                "duplicate",
                existing,
                message="Import GitHub ignore: profil deja associe a l'utilisateur.",
            )
            db.session.commit()
            return jsonify(ok({"id": existing.id, "created": False, "duplicate": True, "profile": developer_payload(existing, _user_id())}))
        developer, created = save_github_profile(username, token=token)
        link_developer_to_user(_user_id(), developer.id, source="github_live")
        log_profile_operation(
            _user_id(),
            "import",
            developer,
            message="Profil importe manuellement depuis la recherche GitHub.",
        )
        db.session.commit()
        return jsonify(ok({"id": developer.id, "created": created, "duplicate": False, "profile": developer_payload(developer, _user_id())}))
    except GitHubRateLimitError as e:
        return jsonify(err(str(e), "github_rate_limit")), 429
    except GitHubLiveSearchError as e:
        return jsonify(err(str(e), "github_api_error")), 502


@bp.post("/github/users/ignore")
@require_login
def github_user_ignore_api():
    payload = request.get_json(silent=True) or {}
    username = (payload.get("username") or "").strip()
    if not username:
        return jsonify(err("Le nom d'utilisateur est obligatoire.", "validation_error")), 400
    log_profile_operation(
        _user_id(),
        "ignore",
        username=username,
        platform="github",
        message="Profil GitHub ignore manuellement.",
    )
    db.session.commit()
    return jsonify(ok({"ignored": True, "username": username}))


@bp.get("/developers/<int:developer_id>")
@require_login
def developer_details_api(developer_id: int):
    data = developer_details(developer_id, _user_id())
    if not data:
        return jsonify(err("Développeur introuvable.", "not_found")), 404
    return jsonify(ok(data))


@bp.put("/developers/<int:developer_id>")
@require_login
def developer_update_api(developer_id: int):
    payload = request.get_json(silent=True) or {}
    try:
        return jsonify(ok(update_developer_profile(_user_id(), developer_id, payload)))
    except PermissionError as e:
        return jsonify(err(str(e), "forbidden")), 403
    except ValueError as e:
        return jsonify(err(str(e), "validation_error")), 400
    except Exception as e:
        return jsonify(err(str(e), "update_error")), 500


@bp.delete("/developers/<int:developer_id>")
@require_login
def developer_delete_api(developer_id: int):
    payload = request.get_json(silent=True) or {}
    confirm = str(payload.get("confirm") or "").strip().lower()
    if confirm != "delete":
        return jsonify(err("Confirmation obligatoire avant suppression.", "confirmation_required")), 400
    try:
        return jsonify(ok(delete_developer_profile(_user_id(), developer_id)))
    except PermissionError as e:
        return jsonify(err(str(e), "forbidden")), 403
    except Exception as e:
        return jsonify(err(str(e), "delete_error")), 500


@bp.get("/profile-operations")
@require_login
def profile_operations_api():
    try:
        limit = max(1, min(50, int(request.args.get("limit") or 20)))
    except ValueError:
        limit = 20
    return jsonify(ok({"items": recent_profile_operations(_user_id(), limit)}))


@bp.get("/developers/<int:developer_id>/charts")
@require_login
def developer_charts_api(developer_id: int):
    if not user_can_access_developer(_user_id(), developer_id):
        return jsonify(err("Développeur introuvable.", "not_found")), 404
    return jsonify(ok(developer_charts(developer_id, _user_id())))


@bp.get("/developers/<int:developer_id>/repos")
@require_login
def developer_repos_api(developer_id: int):
    if not user_can_access_developer(_user_id(), developer_id):
        return jsonify(err("Développeur introuvable.", "not_found")), 404
    return jsonify(ok({"items": developer_repos(developer_id, _user_id())}))


@bp.get("/favorites")
@require_login
def favorites_api():
    uid = _user_id()
    rows = (
        db.session.query(Favorite.developer_id)
        .filter(Favorite.user_id == uid)
        .all()
    )
    ids = [r[0] for r in rows]
    return jsonify(ok({"developer_ids": ids}))


@bp.get("/favorites/stats")
@require_login
def favorites_stats_api():
    uid = _user_id()
    rows = (
        db.session.query(Developer)
        .join(Favorite, Favorite.developer_id == Developer.id)
        .filter(Favorite.user_id == uid)
        .all()
    )
    total = len(rows)
    avg_followers = sum(d.followers_count or 0 for d in rows) / total if total else 0
    avg_repos = sum(d.repos_count or 0 for d in rows) / total if total else 0
    return jsonify(ok({"total": total, "avg_followers": avg_followers, "avg_repos": avg_repos}))


@bp.post("/favorites/<int:developer_id>")
@require_login
def favorite_add_api(developer_id: int):
    uid = _user_id()
    if not user_can_access_developer(uid, developer_id):
        return jsonify(err("Développeur introuvable.", "not_found")), 404
    exists = Favorite.query.filter_by(user_id=uid, developer_id=developer_id).first()
    if not exists:
        db.session.add(Favorite(user_id=uid, developer_id=developer_id))
        db.session.commit()
    return jsonify(ok({"saved": True}))


@bp.delete("/favorites/<int:developer_id>")
@require_login
def favorite_remove_api(developer_id: int):
    uid = _user_id()
    Favorite.query.filter_by(user_id=uid, developer_id=developer_id).delete()
    db.session.commit()
    return jsonify(ok({"saved": False}))


@bp.post("/etl/run")
@require_login
def etl_run_api():
    payload = request.get_json(silent=True) or {}
    query = (payload.get("query") or "").strip() or "location:Morocco language:Python"
    limit = int(payload.get("limit") or 25)
    limit = max(1, min(50, limit))

    try:
        token = current_app.config.get("GITHUB_TOKEN", "")
        result = run_etl_github(query=query, token=token, limit=limit, user_id=_user_id())
        return jsonify(ok(result))
    except Exception as e:
        return jsonify(err(str(e))), 500


@bp.get("/etl/history")
@require_login
def etl_history_api():
    return jsonify(ok({"items": recent_etl_runs(25, user_id=_user_id())}))


@bp.get("/etl/<int:etl_run_id>/logs")
@require_login
def etl_logs_api(etl_run_id: int):
    run = EtlRun.query.filter_by(id=etl_run_id, user_id=_user_id()).first()
    if not run:
        return jsonify(err("Exécution ETL introuvable.", "not_found")), 404
    return jsonify(ok({"items": etl_run_logs(etl_run_id)}))


@bp.get("/exports/dashboard")
@require_login
def export_dashboard():
    fmt = (request.args.get("format") or "csv").lower()
    rows = (
        db.session.query(Skill.name.label("technology"), db.func.sum(DevSkill.score).label("score"))
        .join(DevSkill, DevSkill.skill_id == Skill.id)
        .join(UserDeveloper, UserDeveloper.developer_id == DevSkill.developer_id)
        .filter(UserDeveloper.user_id == _user_id())
        .group_by(Skill.name)
        .order_by(db.func.sum(DevSkill.score).desc())
        .limit(50)
        .all()
    )
    data = [{"technology": name, "score": int(score)} for name, score in rows]

    try:
        if fmt == "pdf":
            out = export_dashboard_pdf(dashboard_summary(_user_id()), data)
        elif fmt == "xlsx":
            out = export_table_xlsx(data, "dashboard_top_technologies.xlsx")
        else:
            out = export_table_csv(data, "dashboard_top_technologies.csv")
    except Exception as e:
        return jsonify(err(str(e))), 500

    return send_file(
        io.BytesIO(out["bytes"]),
        mimetype=out["mimetype"],
        as_attachment=True,
        download_name=out["filename"],
    )


@bp.get("/exports/developer/<int:developer_id>")
@require_login
def export_developer(developer_id: int):
    fmt = (request.args.get("format") or "pdf").lower()
    data = developer_details(developer_id, _user_id())
    if not data:
        return jsonify(err("Développeur introuvable.", "not_found")), 404

    try:
        if fmt == "csv":
            out = export_table_csv(data.get("skills", []), f"developer_{developer_id}_skills.csv")
        elif fmt == "xlsx":
            out = export_table_xlsx(data.get("skills", []), f"developer_{developer_id}_skills.xlsx")
        else:
            out = export_developer_pdf(data)
    except Exception as e:
        return jsonify(err(str(e))), 500

    return send_file(
        io.BytesIO(out["bytes"]),
        mimetype=out["mimetype"],
        as_attachment=True,
        download_name=out["filename"],
    )
