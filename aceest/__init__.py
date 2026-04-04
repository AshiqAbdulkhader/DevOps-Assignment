from flask import Flask

from aceest.db import close_db, init_db
from aceest.routes import bp as main_bp


def create_app(test_config=None):
    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev-change-in-production",
    )
    if test_config is not None:
        app.config.update(test_config)

    init_db()
    app.teardown_appcontext(close_db)
    app.register_blueprint(main_bp)

    return app
