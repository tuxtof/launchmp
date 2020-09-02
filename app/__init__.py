from flask import Flask
from flask_login import LoginManager
from flask_bootstrap import Bootstrap
from app.config import config


login_manager = LoginManager()
login_manager.login_view = 'auth.login'

bootstrap = Bootstrap()


def create_app():
    # Create application
    app = Flask(__name__)
    app.config.from_object(config)

    from app.base import base as views_blueprint
    app.register_blueprint(views_blueprint)


    # Create admin

    return app
