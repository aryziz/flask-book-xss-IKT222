# auth.py
from flask import Blueprint, request, redirect, url_for, flash, render_template, g, session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import select
from .db import SessionLocal
from .models.user import User
from .security import hash_password, verify_password

bp = Blueprint('auth', __name__)

@bp.before_app_request
def load_user():
    g.db = SessionLocal()
    uid = session.get("uid")
    g.user = g.db.get(User, uid) if uid else None

@bp.teardown_app_request
def close_db(exc=None):
    if hasattr(g, "db"):
        g.db.close()

@bp.route('/register', methods=['GET', 'POST'])
def register():
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
        new_user = User(email=email, password_hash=pw_hash)
        try:
            g.db.add(new_user)
            g.db.commit()
        except IntegrityError:
            g.db.rollback()
            flash("Email already registered.", "error")
            return redirect(url_for("auth.register"))

        session.clear()
        session["uid"] = new_user.id
        flash("Registration successful.", "success")
        return redirect(url_for("web.index"))
    return render_template('register.html')

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = (request.form.get('email') or '').strip().lower()
        password = request.form.get('password') or ''

        user = g.db.execute(select(User).filter_by(email=email)).scalar_one_or_none()
        # FIX: pass (stored_hash, password)
        if user and verify_password(user.password_hash, password):
            session.clear()
            session["uid"] = user.id
            flash("Login successful.", "success")
            return redirect(url_for("web.index"))

        flash("Invalid email or password.", "error")
        return redirect(url_for("auth.login"))
    return render_template('login.html')

@bp.post('/logout')
def logout():
    session.pop("uid", None)
    flash("Logged out.", "ok")
    return redirect(url_for("web.index"))
