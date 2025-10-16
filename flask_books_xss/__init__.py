from flask import Flask, g
from os import getenv
from .db import SessionLocal
from .schema import init_db
from .routes import web
from .auth import bp as auth_bp
from flask_talisman import Talisman
from .utils.limiter import limiter

talisman = Talisman()


CSP = {
    "default-src": "'self'",
    "script-src": ["'self'"],
    "style-src": ["'self'"],
    "object-src": "'none'",
    "base-uri": "'self'",
    "frame-ancestors": "'none'"
}

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = getenv("SECRET_KEY", "dev")
    app.config['VULNERABLE_MODE'] = getenv("VULNERABLE_MODE", "false").lower() == "true"
    
    limiter.init_app(app)
    
    if not app.config["VULNERABLE_MODE"]:
        talisman.init_app(
            app,
            content_security_policy=CSP,
            content_security_policy_nonce_in=["script-src", "style-src"],
            force_https=False,
            session_cookie_secure=True
        )
    init_db()
    
    app.register_blueprint(web, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    
    @app.teardown_appcontext
    def remove_session(exception=None):
        SessionLocal.remove()
        
    return app