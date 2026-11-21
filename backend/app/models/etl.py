from datetime import datetime

from ..extensions import db


class EtlRun(db.Model):
    __tablename__ = "etl_runs"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), index=True)
    source = db.Column(db.String(50), nullable=False)
    query = db.Column(db.String(255))
    extracted_count = db.Column(db.Integer, nullable=False, default=0)
    transformed_count = db.Column(db.Integer, nullable=False, default=0)
    loaded_count = db.Column(db.Integer, nullable=False, default=0)
    created_count = db.Column(db.Integer, nullable=False, default=0)
    updated_count = db.Column(db.Integer, nullable=False, default=0)
    linked_count = db.Column(db.Integer, nullable=False, default=0)
    duplicates_removed = db.Column(db.Integer, nullable=False, default=0)
    missing_values_filled = db.Column(db.Integer, nullable=False, default=0)
    error_count = db.Column(db.Integer, nullable=False, default=0)
    status = db.Column(db.String(20), nullable=False)
    started_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    finished_at = db.Column(db.DateTime)


class EtlLog(db.Model):
    __tablename__ = "etl_logs"

    id = db.Column(db.Integer, primary_key=True)
    etl_run_id = db.Column(
        db.Integer, db.ForeignKey("etl_runs.id", ondelete="CASCADE"), nullable=False
    )
    level = db.Column(db.String(10), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    etl_run = db.relationship(
        "EtlRun", backref=db.backref("logs", cascade="all, delete-orphan")
    )


class SearchHistory(db.Model):
    __tablename__ = "search_history"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    q = db.Column(db.String(255), default="")
    technologies = db.Column(db.String(255), default="")
    platform = db.Column(db.String(50), default="")
    activity = db.Column(db.String(30), default="")
    location = db.Column(db.String(150), default="")
    recent_days = db.Column(db.Integer)
    min_repos = db.Column(db.Integer)
    max_repos = db.Column(db.Integer)
    min_followers = db.Column(db.Integer)
    max_followers = db.Column(db.Integer)
    sort = db.Column(db.String(30), default="activity")
    order = db.Column(db.String(10), default="desc")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
