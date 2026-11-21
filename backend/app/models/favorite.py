from datetime import datetime

from ..extensions import db


class Favorite(db.Model):
    __tablename__ = "favorites"

    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    developer_id = db.Column(
        db.Integer, db.ForeignKey("developers.id", ondelete="CASCADE"), primary_key=True
    )
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
