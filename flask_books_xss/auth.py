# auth.py
from flask import Blueprint, request, redirect, url_for, flash, render_template, g, session, Response
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from .db import SessionLocal
from .models.user import User
from .security import hash_password, verify_password
from .utils.limiter import limiter

bp = Blueprint('auth', __name__)

@bp.before_app_request
def load_user() -> None:
    """Load user before each request.
    """
    g.db = SessionLocal()
    uid = session.get("uid")
    g.user = g.db.get(User, uid) if uid else None

@bp.teardown_app_request
def close_db(exc=None):
    if hasattr(g, "db"):
        g.db.close()

@bp.route('/register', methods=['GET', 'POST'])
def register() -> Response:
    """User registering route

    Returns:
        Response: Flask Response object
    """
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        if not email or not password:
            flash("Email and password are required.", "error")
            return redirect(url_for("auth.register"))
        if len(password) < 8:
            flash("Password must be at least 8 characters long.", "error")
            return redirect(url_for("auth.register"))

        pw_hash = hash_password(password)
        new_user = User(email=email, password_hash=pw_hash, failed_attempts=0)
        try:
            g.db.add(new_user)
            g.db.commit()
        except IntegrityError as e:
            g.db.rollback()
            print(e)
            flash("Email already registered.", "error")
            return redirect(url_for("auth.register"))

        session.clear()
        session["uid"] = new_user.id
        flash("Registration successful.", "success")
        return redirect(url_for("web.index"))
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("10 per minute")
def login() -> Response:
    """Login route

    Returns:
        Response: Flask Response object
    """
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''
        
        from .users import authenticate
        user = authenticate(email, password)
        if not user:
            flash("Invalid email or password.", "error")
            return redirect(url_for("auth.login"))
        session.clear()
        session["uid"] = user.id
        flash("Logged in successfully.", "ok")
        return redirect(url_for("web.index"))
    return render_template('login.html')

@bp.post('/logout')
def logout() -> Response:
    session.pop("uid", None)
    flash("Logged out.", "ok")
    return redirect(url_for("web.index"))
