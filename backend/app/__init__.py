import sys
import warnings

from flask import Flask

sys.dont_write_bytecode = True

warnings.filterwarnings(
    "ignore",
    message=r"urllib3 .*doesn't match a supported version!",
    module=r"requests",
)

from .config import Config
from .extensions import db
from .routes.admin import bp as admin_bp
from .routes.api import bp as api_bp
from .routes.auth import bp as auth_bp
from .routes.pages import bp as pages_bp
from .ml.comparison_routes import ml_bp as ml_bp
from .services.schema_migration import ensure_schema


def create_app() -> Flask:
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        static_url_path="/static",
    )
    app.config.from_object(Config())

    db.init_app(app)
    with app.app_context():
        db.create_all()
        ensure_schema()

    app.register_blueprint(auth_bp)
    app.register_blueprint(pages_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(ml_bp, url_prefix="/ml")

    from .routes.errors import register_error_handlers

    register_error_handlers(app)

    return app
