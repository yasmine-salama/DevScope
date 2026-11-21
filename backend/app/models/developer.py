from datetime import datetime

from ..extensions import db


class Developer(db.Model):
    __tablename__ = "developers"

    id = db.Column(db.Integer, primary_key=True)
    platform = db.Column(db.String(30), nullable=False)
    username = db.Column(db.String(100), nullable=False)
    display_name = db.Column(db.String(150))
    avatar_url = db.Column(db.Text)
    bio = db.Column(db.Text)
    profile_url = db.Column(db.Text, nullable=False)
    location = db.Column(db.String(150))
    followers_count = db.Column(db.Integer, nullable=False, default=0)
    repos_count = db.Column(db.Integer, nullable=False, default=0)
    last_activity_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime)
    updated_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    contributions_last_year = db.Column(db.Integer, nullable=False, default=0)
    raw_json = db.Column(db.Text)

    __table_args__ = (db.UniqueConstraint("platform", "username", name="uq_platform_username"),)


class UserDeveloper(db.Model):
    __tablename__ = "user_developers"

    user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True
    )
    developer_id = db.Column(
        db.Integer, db.ForeignKey("developers.id", ondelete="CASCADE"), primary_key=True
    )
    source = db.Column(db.String(50), nullable=False, default="manual")
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    developer = db.relationship("Developer", backref=db.backref("user_links", cascade="all, delete-orphan"))


class Skill(db.Model):
    __tablename__ = "skills"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), unique=True, nullable=False)


class DevSkill(db.Model):
    __tablename__ = "dev_skills"

    developer_id = db.Column(
        db.Integer, db.ForeignKey("developers.id", ondelete="CASCADE"), primary_key=True
    )
    skill_id = db.Column(
        db.Integer, db.ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True
    )
    score = db.Column(db.Integer, nullable=False, default=0)
    source = db.Column(db.String(50), nullable=False, default="api")

    developer = db.relationship("Developer", backref=db.backref("dev_skills", cascade="all, delete-orphan"))
    skill = db.relationship("Skill")
