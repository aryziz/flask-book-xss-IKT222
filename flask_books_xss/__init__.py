from flask import Flask
from os import getenv
from .db import init_db, SessionLocal
from .routes import web

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = getenv("SECRET_KEY", "dev")
    app.config['VULNERABLE_MODE'] = getenv("VULNERABLE_MODE", "false").lower() == "true"
    init_db()
    
    app.register_blueprint(web, url_prefix='/')
    
    @app.teardown_appcontext
    def remove_session(exception=None):
        SessionLocal.remove()
        
    return app