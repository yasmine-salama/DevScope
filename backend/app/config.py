import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv


def _first_non_empty(*values: object, default: str = "") -> str:
    for value in values:
        text = str(value or "").strip()
        if text:
            return text
    return default


class Config:
    def __init__(self) -> None:
        backend_dir = Path(__file__).resolve().parents[1]
        project_dir = backend_dir.parent
        backend_env = backend_dir / ".env"
        project_env = project_dir / ".env"
        load_dotenv(project_env, override=False)
        load_dotenv(backend_env, override=False)
        backend_values = dotenv_values(backend_env)
        project_values = dotenv_values(project_env)

        secret_key = _first_non_empty(
            os.getenv("SECRET_KEY"),
            backend_values.get("SECRET_KEY"),
            project_values.get("SECRET_KEY"),
        )
        placeholders = {
            "dev", "change_me", "changeme", "secret",
            "replace_with_a_random_64_character_hex_value",
            "paste_a_new_random_secret_here",
        }
        if not secret_key or secret_key.lower() in placeholders or len(secret_key) < 32:
            raise RuntimeError(
                "Set a strong SECRET_KEY (at least 32 characters) in backend/.env. "
                "Generate one with: python -c \"import secrets; print(secrets.token_hex(32))\""
            )
        self.SECRET_KEY = secret_key
        self.SESSION_COOKIE_HTTPONLY = True
        self.SESSION_COOKIE_SAMESITE = "Lax"
        self.SESSION_COOKIE_SECURE = os.getenv("SESSION_COOKIE_SECURE", "false").lower() in {
            "1", "true", "yes"
        }
        self.SQLALCHEMY_DATABASE_URI = _first_non_empty(
            os.getenv("DATABASE_URL"),
            backend_values.get("DATABASE_URL"),
            project_values.get("DATABASE_URL"),
            default="sqlite:///devscope.db",
        )
        self.SQLALCHEMY_TRACK_MODIFICATIONS = False

        self.GITHUB_TOKEN = _first_non_empty(
            os.getenv("GITHUB_TOKEN"),
            backend_values.get("GITHUB_TOKEN"),
            project_values.get("GITHUB_TOKEN"),
        )
