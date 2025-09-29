from flask import request, render_template, redirect, url_for
from dotenv import load_dotenv
from flask_talisman import Talisman
from . import create_app
from .storage import add_book, list_books

load_dotenv()
app = create_app()

# if not app.config["VULNERABLE_MODE"]:
#     Talisman(app, content_security_policy = {
#         "default-src": "'self'",
#         "script-src": "'self'",
#         "style-src": "'self'"
#     })
    
def main():
    app.run(debug=True)
