from __future__ import annotations
import os, io
from typing import Optional

from flask import (
    Blueprint, request, redirect, url_for, flash, render_template_string, session, send_file
)

mfa_bp = Blueprint("mfa", __name__, url_prefix="/auth")

from .db import SessionLocal, engine

from .utils.limiter import limiter  

from .models.user import User  

try:
    from .users import authenticate
    HAVE_AUTHENTICATE = True
except Exception:
    from .security import verify_password
    HAVE_AUTHENTICATE = False

REQUIRE_2FA = os.getenv("REQUIRE_2FA", "false").lower() == "true"

from sqlalchemy import Column, Integer, String, ForeignKey

from .models.base import Base

class UserMFA(Base):
    __tablename__ = "user_mfa"
    user_id = Column(Integer, ForeignKey("user.id", ondelete="CASCADE"), primary_key=True)
    secret  = Column(String(64), nullable=False, unique=True)

UserMFA.__table__.create(bind=engine, checkfirst=True)

import pyotp
import qrcode

ISSUER = "IKT222-BookApp"  

def _get_user_by_email(email: str) -> Optional[User]:
    with SessionLocal() as s:
        return s.query(User).filter(User.email == email).first()

def _get_user_by_id(uid: int) -> Optional[User]:
    with SessionLocal() as s:
        return s.get(User, uid)

def _get_secret(uid: int) -> Optional[str]:
    with SessionLocal() as s:
        row = s.get(UserMFA, uid)
        return row.secret if row else None

def _get_or_create_secret(uid: int) -> str:
    with SessionLocal() as s:
        row = s.get(UserMFA, uid)
        if row and row.secret:
            return row.secret
        secret = pyotp.random_base32()
        s.merge(UserMFA(user_id=uid, secret=secret))
        s.commit()
        return secret


@mfa_bp.route("/mfa/enable", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def mfa_enable():
    uid = session.get("uid")
    if not uid:
        flash("Log in first to enable 2FA.", "error")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        _get_or_create_secret(uid)
        flash("2FA enabled. Scan the QR with your Authenticator app.", "ok")
        return redirect(url_for("mfa.mfa_enable"))

    user = _get_user_by_id(uid)
    secret = _get_secret(uid)
    return render_template_string(
        """<!doctype html>
        <h1>Two-Factor Authentication (TOTP)</h1>
        {% if secret %}
          <p>2FA is <strong>enabled</strong> for {{ user.email }}.</p>
          <p>Scan this QR code with Authenticator:</p>
          <img alt="TOTP QR" src="{{ url_for('mfa.mfa_qr') }}">
          <p>Or enter this secret manually: <code>{{ secret }}</code></p>
          <details><summary>Confirm setup (recommended)</summary>
            <form method="post" action="{{ url_for('mfa.mfa_confirm') }}">
              <input name="code" pattern="\\d{6}" inputmode="numeric" maxlength="6" placeholder="123456" required>
              <button>Confirm</button>
            </form>
          </details>
        {% else %}
          <p>2FA is currently <strong>disabled</strong>.</p>
          <form method="post"><button type="submit">Enable 2FA (generate secret)</button></form>
        {% endif %}""",
        user=user, secret=secret
    )

@mfa_bp.get("/mfa/qr")
def mfa_qr():
    uid = session.get("uid")
    if not uid:
        flash("Log in first.", "error")
        return redirect(url_for("auth.login"))

    user = _get_user_by_id(uid)
    secret = _get_secret(uid)
    if not user or not secret:
        flash("Enable 2FA first.", "error")
        return redirect(url_for("mfa.mfa_enable"))

    uri = pyotp.TOTP(secret).provisioning_uri(name=user.email, issuer_name=ISSUER)
    img = qrcode.make(uri)
    buf = io.BytesIO(); img.save(buf, format="PNG"); buf.seek(0)
    return send_file(buf, mimetype="image/png")

@mfa_bp.post("/mfa/confirm")
@limiter.limit("5 per minute")
def mfa_confirm():
    uid = session.get("uid")
    if not uid:
        flash("Log in first.", "error")
        return redirect(url_for("auth.login"))

    secret = _get_secret(uid)
    if not secret:
        flash("Enable 2FA first.", "error")
        return redirect(url_for("mfa.mfa_enable"))

    code = (request.form.get("code") or "").strip()
    if pyotp.TOTP(secret).verify(code, valid_window=1):
        flash("2FA setup confirmed.", "ok")
    else:
        flash("Invalid or expired code.", "error")
    return redirect(url_for("mfa.mfa_enable"))

@mfa_bp.route("/login-totp", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def login_totp():
    """
    Step 1: email/password. If the account has a TOTP secret (or REQUIRE_2FA),
    redirect to /auth/verify. Otherwise, log in directly.
    """
    if request.method == "GET":
        return render_template_string(
            """<!doctype html>
            <h1>Login (with 2FA)</h1>
            <form method="post">
              <label>Email <input name="email" type="email" required></label><br>
              <label>Password <input name="password" type="password" required></label><br>
              <button>Continue</button>
            </form>
            <p>Want to enable 2FA? <a href="{{ url_for('mfa.mfa_enable') }}">enable here</a>.</p>"""
        )

    email = (request.form.get("email") or "").strip().lower()
    password = request.form.get("password") or ""

    if HAVE_AUTHENTICATE:
        user = authenticate(email, password)  
        if not user:
            flash("Invalid email or password.", "error")
            return redirect(url_for("mfa.login_totp"))
        u = _get_user_by_id(user.id)  
    else:
        u = _get_user_by_email(email)
        if not u:
            flash("Invalid email or password.", "error")
            return redirect(url_for("mfa.login_totp"))
        if not verify_password(u.password_hash, password):  
            flash("Invalid email or password.", "error")
            return redirect(url_for("mfa.login_totp"))

    has_secret = bool(_get_secret(u.id))
    if REQUIRE_2FA and not has_secret:
        session.clear(); session["uid"] = u.id
        flash("2FA required. Please enable first.", "error")
        return redirect(url_for("mfa.mfa_enable"))

    if has_secret:
        session.clear()
        session["mfa_pending_uid"] = u.id
        flash("Password OK. Enter your 6-digit code.", "ok")
        return redirect(url_for("mfa.verify_totp"))

    session.clear(); session["uid"] = u.id
    flash("Logged in successfully.", "ok")
    return redirect(url_for("web.index"))

@mfa_bp.route("/verify", methods=["GET", "POST"])
@limiter.limit("10 per minute")
def verify_totp():
    pending_uid = session.get("mfa_pending_uid")
    if not pending_uid:
        flash("Start with email & password.", "error")
        return redirect(url_for("mfa.login_totp"))

    if request.method == "GET":
        return render_template_string(
            """<!doctype html>
            <h1>Enter 2FA code</h1>
            <form method="post">
              <input name="code" pattern="\\d{6}" inputmode="numeric" maxlength="6" placeholder="123456" required>
              <button>Verify</button>
            </form>"""
        )

    secret = _get_secret(pending_uid)
    if not secret:
        flash("2FA not enabled for this account.", "error")
        return redirect(url_for("mfa.login_totp"))

    code = (request.form.get("code") or "").strip()
    ok = pyotp.TOTP(secret).verify(code, valid_window=1)
    if not ok:
        flash("Invalid or expired code.", "error")
        return redirect(url_for("mfa.verify_totp"))

    session.clear(); session["uid"] = pending_uid
    flash("2FA verified. You are now logged in.", "ok")
    return redirect(url_for("web.index"))

@mfa_bp.post("/mfa/disable")
def mfa_disable():
    uid = session.get("uid")
    if not uid:
        flash("Log in first.", "error")
        return redirect(url_for("auth.login"))

    with SessionLocal() as s:
        row = s.get(UserMFA, uid)
        if row:
            s.delete(row); s.commit()
    flash("2FA disabled for your account.", "ok")
    return redirect(url_for("mfa.mfa_enable"))
