import json
from datetime import datetime
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app

from ..models.developer import Developer
from ..services.auth_service import require_login
from ..services.auth_service import current_user
from .feature_engineering import load_developers_dataframe, compute_scores, top_skills
from .model_training import train_and_evaluate, load_saved_model
from .matching_service import match_job



ml_bp = Blueprint("ml", __name__)


@ml_bp.route("/")
@require_login
def index():
    return redirect(url_for("ml.compare"))


@ml_bp.route("/dashboard")
@require_login
def dashboard():
    # Dashboard removed — redirect to compare UI
    return redirect(url_for("ml.compare"))


@ml_bp.route("/train", methods=["GET", "POST"])
@require_login
def train():
    user = current_user()
    res = train_and_evaluate(user_id=user.id if user else None)
    if res.get("error"):
        flash("Échec de l'entraînement : %s" % res.get("error"), "error")
    else:
        flash("Training terminé. Meilleur modèle: %s" % res.get("best", {}).get("name", "-"), "success")
    return redirect(url_for("ml.compare"))


@ml_bp.route("/compare", methods=["GET", "POST"])
@require_login
def compare():
    user = current_user()
    user_id = user.id if user else None
    # POST: user submitted selection of profiles to compare
    if request.method == "POST":
        selected = request.form.getlist("ids")
        if not selected:
            flash("Aucun profil sélectionné.", "warning")
            return redirect(url_for("ml.compare"))
        ids_param = ",".join(selected)
        return redirect(url_for("ml.compare", ids=ids_param))

    # GET: either show selection UI (no ids) or comparison (ids provided)
    ids = request.args.get("ids") or request.args.getlist("ids")
    if isinstance(ids, str):
        ids = [s for s in ids.split(",") if s]
    ids = [int(i) for i in ids] if ids else []

    if ids:
        # Prefer loading preprocessed dataframe to compute derived scores
        df = load_developers_dataframe(user_id=user_id)
        df = compute_scores(df) if not df.empty else df

        df_sel = df[df["id"].isin(ids)] if not df.empty else None

        rows = []
        bar_chart = None
        radar_chart = None

        if df_sel is not None and not df_sel.empty:
            # Prepare rows for table
            for _, r in df_sel.iterrows():
                rows.append(
                    {
                        "id": int(r["id"]),
                        "username": r["username"],
                        "display_name": r.get("display_name", ""),
                        "followers_count": int(r.get("followers_count", 0)),
                        "repos_count": int(r.get("repos_count", 0)),
                        "contributions_last_year": int(r.get("contributions_last_year", 0)),
                    }
                )

            # Bar chart: followers / repos / contributions
            names = [str(x) for x in df_sel["username"].tolist()]
            followers = [int(x) for x in df_sel["followers_count"].tolist()]
            repos = [int(x) for x in df_sel["repos_count"].tolist()]
            contribs = [int(x) for x in df_sel["contributions_last_year"].tolist()]

            bar_trace = {
                "data": [
                    {"type": "bar", "name": "Followers", "x": names, "y": followers},
                    {"type": "bar", "name": "Dépôts", "x": names, "y": repos},
                    {"type": "bar", "name": "Contributions (1 an)", "x": names, "y": contribs},
                ],
                "layout": {"title": "Comparaison - Followers / Dépôts / Contributions", "barmode": "group"},
            }

            # Radar chart: compare the normalized scores
            categories = [
                "Popularité",
                "Activité",
                "Contribution",
                "Expérience",
                "Compétences",
            ]
            score_columns = [
                "popularity_score",
                "activity_score",
                "contribution_score",
                "experience_score",
                "skills_score",
            ]

            radar_data = []
            for _, r in df_sel.iterrows():
                vals = [float(r.get(c, 0.0)) for c in score_columns]
                radar_data.append({"type": "scatterpolar", "r": vals + [vals[0]], "theta": categories + [categories[0]], "fill": "toself", "name": str(r["username"])})

            radar_trace = {"data": radar_data, "layout": {"title": "Profil (radar)"}}
            bar_chart = json.dumps(bar_trace)
            radar_chart = json.dumps(radar_trace)

            # Skills frequency and heatmap
            try:
                skills_series = df_sel["skills_list"].explode().dropna().astype(str)
                skill_counts = skills_series.value_counts()
                top_n = min(40, len(skill_counts))
                top_skills = skill_counts.head(top_n).index.tolist()
                top_counts = skill_counts.head(top_n).tolist()

                # bar chart for skills frequency
                skill_bar_trace = {
                    "data": [{"type": "bar", "x": top_skills, "y": top_counts}],
                    "layout": {"title": "Compétences les plus fréquentes (sélection)"},
                }

                # heatmap: skills x profiles presence
                profiles = [str(x) for x in df_sel["username"].tolist()]
                z = []
                for sk in top_skills:
                    row = [1 if (isinstance(skl, list) and sk in skl) or (isinstance(skl, str) and sk == skl) else 0 for skl in df_sel["skills_list"].tolist()]
                    z.append(row)

                skill_heatmap_trace = {
                    "data": [{"z": z, "x": profiles, "y": top_skills, "type": "heatmap", "colorscale": "Viridis"}],
                    "layout": {"title": "Heatmap des compétences (présence)"},
                }

                skill_bar_chart = json.dumps(skill_bar_trace)
                skill_heatmap = json.dumps(skill_heatmap_trace)
            except Exception:
                skill_bar_chart = None
                skill_heatmap = None

        else:
            # Fallback to DB query if preprocessing missing
            developers = load_developers_dataframe(user_id=user_id)
            developers = developers[developers["id"].isin(ids)] if not developers.empty else developers
            for _, d in developers.iterrows():
                rows.append(
                    {
                        "id": int(d["id"]),
                        "username": d["username"],
                        "display_name": d.get("display_name", ""),
                        "followers_count": int(d.get("followers_count", 0)),
                        "repos_count": int(d.get("repos_count", 0)),
                        "contributions_last_year": int(d.get("contributions_last_year", 0)),
                    }
                )

        return render_template(
            "ml/compare.html",
            developers=rows,
            comparing=True,
            bar_chart=bar_chart,
            radar_chart=radar_chart,
            skill_bar_chart=skill_bar_chart,
            skill_heatmap=skill_heatmap,
        )

    # No ids: show selection list
    all_devs = load_developers_dataframe(user_id=user_id).sort_values("id")
    rows = []
    for _, d in all_devs.iterrows():
        rows.append({
            "id": int(d["id"]),
            "username": d["username"],
            "display_name": d.get("display_name", ""),
            "followers_count": int(d.get("followers_count", 0)),
            "repos_count": int(d.get("repos_count", 0)),
            "contributions_last_year": int(d.get("contributions_last_year", 0)),
        })

    return render_template("ml/compare.html", developers=rows, comparing=False)


@ml_bp.route("/match", methods=["GET", "POST"])
@require_login
def match():
    user = current_user()
    user_id = user.id if user else None
    results = []
    # default form values
    form_values = {
        "title": "",
        "technologies": "",
        "skills": "",
        "experience": "mid",
        "top_n": 50,
        "weight_skill": 0.5,
        "weight_ml": 0.3,
        "weight_experience": 0.2,
    }

    if request.method == "POST":
        form_values["title"] = request.form.get("title", "")
        form_values["technologies"] = request.form.get("technologies", "")
        form_values["skills"] = request.form.get("skills", "")
        form_values["experience"] = request.form.get("experience", "mid")
        form_values["top_n"] = int(request.form.get("top_n", 50))
        try:
            form_values["weight_skill"] = float(request.form.get("weight_skill", 0.5))
            form_values["weight_ml"] = float(request.form.get("weight_ml", 0.3))
            form_values["weight_experience"] = float(request.form.get("weight_experience", 0.2))
        except Exception:
            pass

        techs_list = [t.strip() for t in form_values["technologies"].split(",") if t.strip()]
        skills_list = [s.strip() for s in form_values["skills"].split(",") if s.strip()]

        # Use DB-only matching (GitHub live removed)
        results = match_job(
            form_values["title"],
            techs_list,
            skills_list,
            experience_level=form_values["experience"],
            top_n=form_values["top_n"],
            weight_skill=form_values["weight_skill"],
            weight_ml=form_values["weight_ml"],
            weight_experience=form_values["weight_experience"],
            live_profiles=None,
            user_id=user_id,
        )

    # DB-only results
    db_results = results or []
    live_results = []

    return render_template("ml/match.html", db_results=db_results, live_results=live_results, form=form_values)
