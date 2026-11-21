import os
import tempfile
import unittest
from datetime import datetime
from unittest.mock import patch


fd, db_path = tempfile.mkstemp(prefix="devscope_audit_", suffix=".db")
os.close(fd)
os.environ["DATABASE_URL"] = "sqlite:///" + db_path.replace("\\", "/")
os.environ["SECRET_KEY"] = "audit-secret-for-local-functional-tests-32chars"

from app import create_app
from app.config import Config
from app.extensions import db
from app.models import Developer, DevSkill, Skill, UserDeveloper, User
from app.routes.auth import _safe_next_url


class FunctionalAuditTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = create_app()
        cls.app.config["TESTING"] = True

    def test_config_rejects_example_secret_key(self):
        placeholder = "replace_with_a_random_64_character_hex_value"
        with patch.dict(os.environ, {"SECRET_KEY": placeholder}):
            with self.assertRaises(RuntimeError):
                Config()

    def test_admin_email_environment_variable_does_not_grant_privileges(self):
        with patch.dict(os.environ, {"ADMIN_EMAIL": "u1@example.com"}):
            with self.app.app_context():
                from app.services.schema_migration import ensure_schema
                ensure_schema()
                user = User.query.filter_by(email="u1@example.com").one()
                self.assertFalse(user.is_admin)

    @classmethod
    def tearDownClass(cls):
        try:
            os.remove(db_path)
        except OSError:
            pass

    def setUp(self):
        with self.app.app_context():
            db.drop_all()
            db.create_all()
        self.c1 = self.app.test_client()
        self.c2 = self.app.test_client()
        self._register(self.c1, "u1@example.com")
        self._register(self.c2, "u2@example.com")

    def _register(self, client, email):
        return client.post(
            "/register",
            data={"email": email, "password": "Password123", "confirm_password": "Password123"},
            follow_redirects=True,
        )

    def _seed_developer(self, user_id, username, followers=10, repos=5, skills=None):
        with self.app.app_context():
            dev = Developer(
                platform="github",
                username=username,
                display_name=username.title(),
                profile_url=f"https://github.com/{username}",
                followers_count=followers,
                repos_count=repos,
                location="Morocco",
                bio="Bio",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                last_activity_at=datetime.utcnow(),
                contributions_last_year=25,
            )
            db.session.add(dev)
            db.session.flush()
            db.session.add(UserDeveloper(user_id=user_id, developer_id=dev.id, source="test"))
            for skill_name in skills or ["Python"]:
                skill = Skill.query.filter_by(name=skill_name).first() or Skill(name=skill_name)
                db.session.add(skill)
                db.session.flush()
                db.session.add(DevSkill(developer_id=dev.id, skill_id=skill.id, score=3, source="test"))
            db.session.commit()
            return dev.id

    def test_auth_dashboard_search_favorites_are_user_isolated(self):
        with self.app.app_context():
            self.assertFalse(User.query.filter_by(email="u1@example.com").one().is_admin)
        dev1 = self._seed_developer(1, "alice_dev", skills=["Python"])
        self._seed_developer(2, "bob_dev", skills=["Java"])

        r1 = self.c1.get("/api/search?q=alice")
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.json["data"]["total"], 1)
        self.assertEqual(r1.json["data"]["items"][0]["username"], "alice_dev")

        r2 = self.c2.get("/api/search?q=alice")
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.json["data"]["total"], 0)

        self.assertEqual(self.c1.post(f"/api/favorites/{dev1}").status_code, 200)
        self.assertEqual(self.c2.post(f"/api/favorites/{dev1}").status_code, 404)
        self.assertEqual(self.c1.get("/api/favorites").json["data"]["developer_ids"], [dev1])
        self.assertEqual(self.c2.get("/api/favorites").json["data"]["developer_ids"], [])

        self.assertEqual(self.c1.get(f"/developers/{dev1}").status_code, 200)
        self.assertEqual(self.c2.get(f"/developers/{dev1}").status_code, 404)

        summary1 = self.c1.get("/api/dashboard/summary").json["data"]["kpis"]
        summary2 = self.c2.get("/api/dashboard/summary").json["data"]["kpis"]
        self.assertEqual(summary1["total_profiles"], 1)
        self.assertEqual(summary2["total_profiles"], 1)
        self.assertEqual(summary1["favorites_count"], 1)
        self.assertEqual(summary2["favorites_count"], 0)

    def test_login_redirect_rejects_external_destinations(self):
        self.assertEqual(_safe_next_url("/dashboard"), "/dashboard")
        self.assertIsNone(_safe_next_url("https://attacker.example"))
        self.assertIsNone(_safe_next_url("//attacker.example"))
        self.assertIsNone(_safe_next_url("/\\\\attacker.example"))

    def test_etl_continues_after_invalid_candidates_and_links_to_user(self):
        def fake_user(username, token):
            if username == "bad":
                raise RuntimeError("bad profile")
            return {
                "login": username,
                "name": username.title(),
                "avatar_url": "",
                "bio": "Bio",
                "html_url": f"https://github.com/{username}",
                "location": "Morocco",
                "followers": 4,
                "public_repos": 2,
                "created_at": "2024-01-01T00:00:00Z",
            }

        repos = [{"language": "Python", "pushed_at": "2026-01-01T00:00:00Z", "name": "r"}]
        with patch("app.etl.pipeline.search_users", return_value=["bad", "good1", "good2", "good3"]), \
            patch("app.etl.pipeline.fetch_user", side_effect=fake_user), \
            patch("app.etl.pipeline.fetch_repos", return_value=repos), \
            patch("app.etl.pipeline.scrape_contributions_last_year", return_value=7):
            res = self.c1.post("/api/etl/run", json={"query": "location:Morocco", "limit": 2})

        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json["data"]["loaded_count"], 2)
        self.assertEqual(self.c1.get("/api/search?q=good").json["data"]["total"], 2)
        self.assertEqual(self.c2.get("/api/search?q=good").json["data"]["total"], 0)
        history = self.c1.get("/api/etl/history").json["data"]["items"]
        self.assertEqual(history[0]["loaded_count"], 2)

    def test_ml_routes_and_exports_work_on_user_dataset(self):
        dev1 = self._seed_developer(1, "ml_alice", followers=15, repos=8, skills=["Python", "Flask"])
        self._seed_developer(2, "ml_bob", followers=99, repos=30, skills=["Java"])

        self.assertEqual(self.c1.get("/ml/compare").status_code, 200)
        self.assertEqual(self.c1.get(f"/ml/compare?ids={dev1}").status_code, 200)
        match = self.c1.post(
            "/ml/match",
            data={"title": "Backend", "technologies": "Python", "skills": "Flask", "experience": "mid", "top_n": "5"},
        )
        self.assertEqual(match.status_code, 200)

        pdf = self.c1.get("/api/exports/dashboard?format=pdf")
        self.assertEqual(pdf.status_code, 200)
        self.assertIn("application/pdf", pdf.content_type)

        xlsx = self.c1.get("/api/exports/dashboard?format=xlsx")
        self.assertEqual(xlsx.status_code, 200)
        self.assertIn("spreadsheetml", xlsx.content_type)

        dev_pdf = self.c1.get(f"/api/exports/developer/{dev1}?format=pdf")
        self.assertEqual(dev_pdf.status_code, 200)

        forbidden = self.c2.get(f"/api/exports/developer/{dev1}?format=pdf")
        self.assertEqual(forbidden.status_code, 404)


if __name__ == "__main__":
    unittest.main(verbosity=2)
