from flask import Blueprint, abort, redirect, render_template, url_for

from ..services.auth_service import current_user, is_admin, is_logged_in, require_login
from ..services.user_data_service import user_can_access_developer

bp = Blueprint("pages", __name__)


@bp.app_context_processor
def inject_globals():
    return {"current_user": current_user(), "is_logged_in": is_logged_in(), "is_admin": is_admin()}


@bp.get("/")
def index():
    if is_logged_in():
        return redirect(url_for("pages.dashboard"))
    return redirect(url_for("auth.login"))


@bp.get("/dashboard")
@require_login
def dashboard():
    return render_template("dashboard.html")


@bp.get("/search")
@require_login
def search():
    return render_template("search.html")


@bp.get("/developers/<int:developer_id>")
@require_login
def developer_details(developer_id: int):
    user = current_user()
    if not user_can_access_developer(user.id if user else None, developer_id):
        abort(404)
    return render_template("developer_details.html", developer_id=developer_id)


@bp.get("/favorites")
@require_login
def favorites():
    return render_template("favorites.html")


@bp.get("/etl/history")
@require_login
def etl_history():
    return render_template("etl_history.html")


@bp.get("/exports")
@require_login
def exports():
    return render_template("exports.html")


@bp.get("/profile")
@require_login
def profile():
    return render_template("profile.html")
