from urllib.parse import urlsplit

from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from ..models import User
from ..services.auth_service import (
    authenticate_user,
    create_user,
    validate_email,
    validate_password,
)

bp = Blueprint("auth", __name__)


def _safe_next_url(target):
    """Accept only same-site absolute paths; reject external and protocol-relative URLs."""
    if not target or not target.startswith("/") or target.startswith("//") or "\\\\" in target:
        return None
    parsed = urlsplit(target)
    if parsed.scheme or parsed.netloc:
        return None
    return target


@bp.get("/login")
def login():
    return render_template("auth/login.html")


@bp.post("/login")
def login_post():
    email = request.form.get("email", "")
    password = request.form.get("password", "")

    user = authenticate_user(email=email, password=password)
    if not user:
        flash("Email ou mot de passe invalide.", "danger")
        return redirect(url_for("auth.login"))

    session.clear()
    session["user_id"] = user.id
    flash("Bon retour !", "success")

    next_url = _safe_next_url(request.args.get("next", ""))
    return redirect(next_url or url_for("pages.dashboard"))


@bp.get("/register")
def register():
    return render_template("auth/register.html")


@bp.post("/register")
def register_post():
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")
    confirm = request.form.get("confirm_password", "")

    if not validate_email(email):
        flash("Veuillez saisir une adresse email valide.", "warning")
        return redirect(url_for("auth.register"))

    if not validate_password(password):
        flash("Le mot de passe doit contenir au moins 8 caractères.", "warning")
        return redirect(url_for("auth.register"))

    if password != confirm:
        flash("Les mots de passe ne correspondent pas.", "warning")
        return redirect(url_for("auth.register"))

    if User.query.filter_by(email=email).first():
        flash("Cet email est déjà enregistré.", "warning")
        return redirect(url_for("auth.register"))

    user = create_user(email=email, password=password)
    session.clear()
    session["user_id"] = user.id
    flash("Compte créé avec succès.", "success")
    return redirect(url_for("pages.dashboard"))


@bp.get("/logout")
def logout():
    session.clear()
    flash("Vous avez été déconnecté.", "success")
    return redirect(url_for("auth.login"))
