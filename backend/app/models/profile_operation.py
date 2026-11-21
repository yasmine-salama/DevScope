from datetime import datetime

from ..extensions import db


class ProfileOperation(db.Model):
    __tablename__ = "profile_operations"

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    developer_id = db.Column(db.Integer, db.ForeignKey("developers.id", ondelete="SET NULL"), index=True)
    username = db.Column(db.String(100), nullable=False, default="")
    platform = db.Column(db.String(30), nullable=False, default="github")
    operation = db.Column(db.String(30), nullable=False)
    message = db.Column(db.Text, nullable=False, default="")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

