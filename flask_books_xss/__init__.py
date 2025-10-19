from flask import Flask, g
from os import getenv
import os
from .db import SessionLocal
from .schema import init_db
from .routes import web
from .auth import bp as auth_bp
from flask_talisman import Talisman
from .oauth import bp as oauth2_bp  # <— NEW import
from dotenv import load_dotenv
load_dotenv() 

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
    
    if not app.config["VULNERABLE_MODE"]:
        talisman.init_app(
            app,
            content_security_policy=CSP,
            content_security_policy_nonce_in=["script-src", "style-src"],
            force_https=False,
            session_cookie_secure=True      # <--- turn off in local dev.
        )
    init_db()

    
    #app config for github auth
    app.config['OAUTH2_PROVIDERS'] = {
        'github': {
            'client_id': os.environ.get('OAUTH_CLIENT_ID'),
            'client_secret': os.environ.get('OAUTH_CLIENT_SECRET'),
            'authorize_url': 'https://github.com/login/oauth/authorize',
            'token_url': 'https://github.com/login/oauth/access_token',
            'userinfo': {
                'url': 'https://api.github.com/user/emails',
                'email': lambda json: json[0]['email'],
            },
            'scopes': ['user:email'],
        },
    }

    app.register_blueprint(web, url_prefix='/')
    app.register_blueprint(auth_bp, url_prefix='/auth')
    app.register_blueprint(oauth2_bp, url_prefix='/oauth') 


    
    @app.teardown_appcontext
    def remove_session(exception=None):
        SessionLocal.remove()

        
    return app