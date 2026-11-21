"""Admin area (read-only monitoring) guarded by require_admin."""

from flask import Blueprint, render_template
from sqlalchemy import func

from ..extensions import db
from ..models import DevSkill, Developer, EtlLog, EtlRun, Favorite, Skill, User
from ..services.auth_service import require_admin

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/")
@require_admin
def dashboard():
    counts = {
        "users": db.session.query(func.count(User.id)).scalar() or 0,
        "developers": db.session.query(func.count(Developer.id)).scalar() or 0,
        "skills": db.session.query(func.count(Skill.id)).scalar() or 0,
        "favorites": db.session.query(func.count(Favorite.id)).scalar() or 0,
        "etl_runs": db.session.query(func.count(EtlRun.id)).scalar() or 0,
        "etl_logs": db.session.query(func.count(EtlLog.id)).scalar() or 0,
    }

    recent_users = User.query.order_by(User.created_at.desc()).limit(10).all()
    recent_profiles = Developer.query.order_by(Developer.updated_at.desc()).limit(10).all()
    recent_etl = db.session.query(EtlRun).order_by(EtlRun.started_at.desc()).limit(10).all()

    return render_template(
        "admin/dashboard.html",
        counts=counts,
        recent_users=recent_users,
        recent_profiles=recent_profiles,
        recent_etl=recent_etl,
    )


@bp.get("/users")
@require_admin
def users():
    users = User.query.order_by(User.created_at.desc()).all()
    return render_template("admin/users.html", users=users)


@bp.get("/profiles")
@require_admin
def profiles():
    profiles = Developer.query.order_by(Developer.updated_at.desc()).limit(250).all()
    return render_template("admin/profiles.html", profiles=profiles)


@bp.get("/etl")
@require_admin
def etl():
    runs = db.session.query(EtlRun).order_by(EtlRun.started_at.desc()).limit(100).all()
    logs = EtlLog.query.order_by(EtlLog.created_at.desc()).limit(120).all()
    return render_template("admin/etl.html", runs=runs, logs=logs)


@bp.get("/stats")
@require_admin
def stats():
    top_tech = (
        db.session.query(Skill.name.label("technology"), func.sum(DevSkill.score).label("score"))
        .join(DevSkill, DevSkill.skill_id == Skill.id)
        .group_by(Skill.name)
        .order_by(func.sum(DevSkill.score).desc())
        .limit(25)
        .all()
    )
    return render_template("admin/stats.html", top_tech=top_tech)
