import io
from datetime import datetime
from typing import Dict, List

import matplotlib
import pandas as pd

matplotlib.use("Agg")

import matplotlib.pyplot as plt

try:
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.utils import ImageReader
    from reportlab.pdfgen import canvas

    _REPORTLAB_AVAILABLE = True
except Exception:
    _REPORTLAB_AVAILABLE = False


def export_table_csv(rows: List[Dict], filename: str) -> Dict:
    df = pd.DataFrame(rows)
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return {"filename": filename, "bytes": buf.getvalue().encode("utf-8"), "mimetype": "text/csv"}


def export_table_xlsx(rows: List[Dict], filename: str) -> Dict:
    df = pd.DataFrame(rows)
    bio = io.BytesIO()
    with pd.ExcelWriter(bio, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="data")
    return {
        "filename": filename,
        "bytes": bio.getvalue(),
        "mimetype": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }


def _skills_chart_png(skills: List[Dict]) -> io.BytesIO:
    top = skills[:10]
    labels = [s["name"] for s in top] if top else ["Aucune donnée"]
    values = [s["score"] for s in top] if top else [0]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(labels, values, color="#2f6fed")
    ax.set_title("Technologies principales")
    ax.set_ylabel("Score")
    ax.tick_params(axis="x", labelrotation=30)
    fig.tight_layout()

    bio = io.BytesIO()
    fig.savefig(bio, format="png", dpi=160)
    plt.close(fig)
    bio.seek(0)
    return bio


def _top_technologies_chart_png(rows: List[Dict]) -> io.BytesIO:
    """Render a simple bar chart (PNG) for top technologies."""
    top = rows[:12]
    labels = [r.get("technology") for r in top] if top else ["Aucune donnée"]
    values = [r.get("score") for r in top] if top else [0]

    fig, ax = plt.subplots(figsize=(6, 3.5))
    ax.bar(labels, values, color="#2f6fed")
    ax.set_title("Technologies principales")
    ax.set_ylabel("Score")
    ax.tick_params(axis="x", labelrotation=30)
    fig.tight_layout()

    bio = io.BytesIO()
    fig.savefig(bio, format="png", dpi=160)
    plt.close(fig)
    bio.seek(0)
    return bio


def _export_dashboard_pdf_fallback(summary: Dict, top_technologies: List[Dict]) -> Dict:
    from matplotlib.backends.backend_pdf import PdfPages

    bio = io.BytesIO()
    with PdfPages(bio) as pdf:
        k = (summary or {}).get("kpis", {}) if isinstance(summary, dict) else {}
        quality = int(round(((int(k.get("with_location_pct", 0)) + int(k.get("with_bio_pct", 0))) / 2) or 0))

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.1, 0.95, "DevScope · Synthèse du tableau de bord", fontsize=18, weight="bold", va="top")
        fig.text(0.1, 0.92, f"Généré le : {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", fontsize=10, va="top")

        y = 0.86
        for line in [
            f"Profils enregistrés : {int(k.get('total_profiles', 0) or 0)}",
            f"Profils actifs (30 j) : {int(k.get('active_profiles_estimate', 0) or 0)}",
            f"Favoris : {int(k.get('favorites_count', 0) or 0)}",
            f"Qualité des données (localisation/bio) : {quality}%",
        ]:
            fig.text(0.1, y, line, fontsize=12, va="top")
            y -= 0.03

        pdf.savefig(fig)
        plt.close(fig)

        top = top_technologies[:12]
        labels = [r.get("technology") for r in top] if top else ["Aucune donnée"]
        values = [r.get("score") for r in top] if top else [0]

        fig, ax = plt.subplots(figsize=(8.27, 4.6))
        ax.bar(labels, values, color="#2f6fed")
        ax.set_title("Technologies principales")
        ax.set_ylabel("Score")
        ax.tick_params(axis="x", labelrotation=30)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        lines = [f"- {str(r.get('technology', ''))}: {str(r.get('score', ''))}" for r in top_technologies[:40]]
        while lines:
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.text(0.1, 0.95, "Technologies principales (tableau)", fontsize=16, weight="bold", va="top")
            y = 0.9
            for _ in range(45):
                if not lines:
                    break
                fig.text(0.1, y, lines.pop(0), fontsize=10, va="top")
                y -= 0.018
            pdf.savefig(fig)
            plt.close(fig)

    return {"filename": "dashboard_summary.pdf", "bytes": bio.getvalue(), "mimetype": "application/pdf"}


def _export_developer_pdf_fallback(developer: Dict) -> Dict:
    from matplotlib.backends.backend_pdf import PdfPages

    bio = io.BytesIO()
    with PdfPages(bio) as pdf:
        title = developer.get("display_name") or developer.get("username") or "Développeur"

        fig = plt.figure(figsize=(8.27, 11.69))
        fig.text(0.1, 0.95, f"Rapport développeur : {title}", fontsize=18, weight="bold", va="top")
        fig.text(0.1, 0.92, f"Généré le : {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}", fontsize=10, va="top")

        y = 0.86
        for line in [
            f"Plateforme : {developer.get('platform', '')}",
            f"Nom d'utilisateur : {developer.get('username', '')}",
            f"URL du profil : {developer.get('profile_url', '')}",
            f"Localisation : {developer.get('location', '')}",
            f"Followers: {developer.get('followers_count', 0)}",
            f"Dépôts publics : {developer.get('repos_count', 0)}",
            f"Dernière activité : {developer.get('last_activity_at', '')}",
        ]:
            fig.text(0.1, y, line, fontsize=12, va="top")
            y -= 0.03

        pdf.savefig(fig)
        plt.close(fig)

        skills = developer.get("skills", []) or []
        top = skills[:10]
        labels = [s.get("name") for s in top] if top else ["Aucune donnée"]
        values = [s.get("score") for s in top] if top else [0]

        fig, ax = plt.subplots(figsize=(8.27, 4.6))
        ax.bar(labels, values, color="#2f6fed")
        ax.set_title("Compétences principales")
        ax.set_ylabel("Score")
        ax.tick_params(axis="x", labelrotation=30)
        fig.tight_layout()
        pdf.savefig(fig)
        plt.close(fig)

        lines = [f"- {s.get('name','')}: {s.get('score','')}" for s in skills[:60]]
        while lines:
            fig = plt.figure(figsize=(8.27, 11.69))
            fig.text(0.1, 0.95, "Compétences détectées", fontsize=16, weight="bold", va="top")
            y = 0.9
            for _ in range(50):
                if not lines:
                    break
                fig.text(0.1, y, lines.pop(0), fontsize=10, va="top")
                y -= 0.018
            pdf.savefig(fig)
            plt.close(fig)

    return {
        "filename": f"developer_{developer.get('id','')}.pdf",
        "bytes": bio.getvalue(),
        "mimetype": "application/pdf",
    }


def export_dashboard_pdf(summary: Dict, top_technologies: List[Dict]) -> Dict:
    """Generate a lightweight PDF report for the dashboard (KPIs + top technologies)."""
    if not _REPORTLAB_AVAILABLE:
        return _export_dashboard_pdf_fallback(summary, top_technologies)
    bio = io.BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    width, height = A4

    c.setTitle("Rapport du tableau de bord")

    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 60, "DevScope · Synthèse du tableau de bord")

    c.setFont("Helvetica", 10)
    c.drawString(40, height - 80, f"Généré le : {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    k = (summary or {}).get("kpis", {}) if isinstance(summary, dict) else {}
    quality = int(round(((int(k.get("with_location_pct", 0)) + int(k.get("with_bio_pct", 0))) / 2) or 0))

    y = height - 120
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Indicateurs clés")
    y -= 18

    c.setFont("Helvetica", 11)
    lines = [
        f"Profils enregistrés : {int(k.get('total_profiles', 0) or 0)}",
        f"Profils actifs (30 j) : {int(k.get('active_profiles_estimate', 0) or 0)}",
        f"Favoris : {int(k.get('favorites_count', 0) or 0)}",
        f"Qualité des données (localisation/bio) : {quality}%",
    ]
    for line in lines:
        c.drawString(40, y, line)
        y -= 16

    y -= 10
    img = _top_technologies_chart_png(top_technologies)
    c.drawImage(ImageReader(img), 40, y - 240, width=520, height=220, preserveAspectRatio=True, mask="auto")
    y = y - 270

    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Technologies principales (tableau)")
    y -= 18

    c.setFont("Helvetica", 10)
    for r in top_technologies[:25]:
        tech = str(r.get("technology", ""))
        score = str(r.get("score", ""))
        c.drawString(50, y, f"- {tech}: {score}")
        y -= 14
        if y < 60:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)

    c.showPage()
    c.save()

    return {"filename": "dashboard_summary.pdf", "bytes": bio.getvalue(), "mimetype": "application/pdf"}


def export_developer_pdf(developer: Dict) -> Dict:
    if not _REPORTLAB_AVAILABLE:
        return _export_developer_pdf_fallback(developer)
    bio = io.BytesIO()
    c = canvas.Canvas(bio, pagesize=A4)
    width, height = A4

    c.setTitle("Rapport développeur")

    title = developer.get("display_name") or developer.get("username") or "Développeur"
    c.setFont("Helvetica-Bold", 18)
    c.drawString(40, height - 60, f"Rapport développeur : {title}")

    c.setFont("Helvetica", 10)
    c.drawString(40, height - 80, f"Généré le : {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    c.setFont("Helvetica", 12)
    y = height - 120
    lines = [
        f"Plateforme : {developer.get('platform', '')}",
        f"Nom d'utilisateur : {developer.get('username', '')}",
        f"URL du profil : {developer.get('profile_url', '')}",
        f"Localisation : {developer.get('location', '')}",
        f"Followers: {developer.get('followers_count', 0)}",
        f"Dépôts publics : {developer.get('repos_count', 0)}",
        f"Dernière activité : {developer.get('last_activity_at', '')}",
    ]
    for line in lines:
        c.drawString(40, y, line)
        y -= 18

    skills = developer.get("skills", [])
    img = _skills_chart_png(skills)
    c.drawImage(ImageReader(img), 40, y - 240, width=520, height=220, preserveAspectRatio=True, mask="auto")

    y = y - 270
    c.setFont("Helvetica-Bold", 12)
    c.drawString(40, y, "Compétences détectées")
    y -= 18

    c.setFont("Helvetica", 10)
    for s in skills[:20]:
        c.drawString(50, y, f"- {s['name']}: {s['score']}")
        y -= 14
        if y < 60:
            c.showPage()
            y = height - 60
            c.setFont("Helvetica", 10)

    c.showPage()
    c.save()

    return {"filename": f"developer_{developer.get('id','')}.pdf", "bytes": bio.getvalue(), "mimetype": "application/pdf"}
