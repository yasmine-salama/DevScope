from typing import Iterable, List, Tuple

from sqlalchemy import text

from ..extensions import db


def _existing_columns(table: str) -> List[str]:
    rows = db.session.execute(text(f"PRAGMA table_info({table})")).mappings().all()
    return [r["name"] for r in rows]


def _add_columns(table: str, columns: Iterable[Tuple[str, str]]) -> None:
    existing = set(_existing_columns(table))
    for name, ddl in columns:
        if name in existing:
            continue
        db.session.execute(text(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}"))
    db.session.commit()


def _table_exists(table: str) -> bool:
    row = db.session.execute(
        text("SELECT name FROM sqlite_master WHERE type='table' AND name=:name"),
        {"name": table},
    ).first()
    return row is not None


def _ensure_user_tables() -> None:
    db.session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS user_developers (
                user_id INTEGER NOT NULL,
                developer_id INTEGER NOT NULL,
                source VARCHAR(50) NOT NULL DEFAULT 'manual',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (user_id, developer_id),
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(developer_id) REFERENCES developers(id) ON DELETE CASCADE
            )
            """
        )
    )
    db.session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS profile_operations (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                developer_id INTEGER,
                username VARCHAR(100) NOT NULL DEFAULT '',
                platform VARCHAR(30) NOT NULL DEFAULT 'github',
                operation VARCHAR(30) NOT NULL,
                message TEXT NOT NULL DEFAULT '',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE,
                FOREIGN KEY(developer_id) REFERENCES developers(id) ON DELETE SET NULL
            )
            """
        )
    )
    db.session.execute(
        text(
            """
            CREATE TABLE IF NOT EXISTS search_history (
                id INTEGER PRIMARY KEY,
                user_id INTEGER NOT NULL,
                q VARCHAR(255) DEFAULT '',
                technologies VARCHAR(255) DEFAULT '',
                platform VARCHAR(50) DEFAULT '',
                activity VARCHAR(30) DEFAULT '',
                location VARCHAR(150) DEFAULT '',
                recent_days INTEGER,
                min_repos INTEGER,
                max_repos INTEGER,
                min_followers INTEGER,
                max_followers INTEGER,
                sort VARCHAR(30) DEFAULT 'activity',
                "order" VARCHAR(10) DEFAULT 'desc',
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
            )
            """
        )
    )
    db.session.commit()


def _backfill_user_developers() -> None:
    if not _table_exists("user_developers"):
        return
    existing_links = db.session.execute(text("SELECT COUNT(*) FROM user_developers")).scalar() or 0
    if existing_links:
        return

    owner_id = db.session.execute(text("SELECT id FROM users ORDER BY id LIMIT 1")).scalar()
    if not owner_id:
        return

    db.session.execute(
        text(
            """
            INSERT OR IGNORE INTO user_developers (user_id, developer_id, source, created_at)
            SELECT :user_id, id, 'legacy', CURRENT_TIMESTAMP FROM developers
            """
        ),
        {"user_id": owner_id},
    )
    db.session.execute(
        text(
            """
            UPDATE etl_runs
            SET user_id = :user_id
            WHERE user_id IS NULL
            """
        ),
        {"user_id": owner_id},
    )
    db.session.commit()


def ensure_schema() -> None:
    dialect = db.engine.dialect.name
    if dialect != "sqlite":
        return

    _add_columns(
        "users",
        [
            ("is_admin", "INTEGER NOT NULL DEFAULT 0"),
        ],
    )

    _add_columns(
        "developers",
        [
            ("avatar_url", "TEXT"),
            ("bio", "TEXT"),
            ("created_at", "TIMESTAMP"),
            ("contributions_last_year", "INTEGER NOT NULL DEFAULT 0"),
        ],
    )

    _add_columns(
        "etl_runs",
        [
            ("user_id", "INTEGER"),
            ("created_count", "INTEGER NOT NULL DEFAULT 0"),
            ("updated_count", "INTEGER NOT NULL DEFAULT 0"),
            ("linked_count", "INTEGER NOT NULL DEFAULT 0"),
            ("duplicates_removed", "INTEGER NOT NULL DEFAULT 0"),
            ("missing_values_filled", "INTEGER NOT NULL DEFAULT 0"),
            ("error_count", "INTEGER NOT NULL DEFAULT 0"),
        ],
    )

    _ensure_user_tables()
    _backfill_user_developers()
