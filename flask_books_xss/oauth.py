# flask_books_xss/oauth.py
import secrets
from urllib.parse import urlencode
import requests
from datetime import timedelta
from sqlalchemy.exc import IntegrityError
from flask import Blueprint, current_app, abort, redirect, request, session, url_for, flash
from sqlalchemy import select
import secrets
from .db import SessionLocal
from .models.user import User, OAuthAccount
from .utils.time import utc_now
from typing import Dict

bp = Blueprint("oauth2", __name__)  # registered with url_prefix='/oauth' in create_app


def _get_provider(name: str) -> Dict[str, str]:
    p = current_app.config.get('OAUTH2_PROVIDERS', {}).get(name)
    if not p:
        abort(404)
    if not p.get('client_id') or not p.get('client_secret'):
        abort(500, description=f"Provider '{name}' missing client_id/client_secret in environment.")
    return p


@bp.route('/authorize/<provider>')
def oauth2_authorize(provider):
    # Use your existing session-based login flag
    if session.get("uid"):
        return redirect(url_for('web.index'))

    provider_data = _get_provider(provider)

    # CSRF state
    session['oauth2_state'] = secrets.token_urlsafe(16)

    qs = urlencode({
        'client_id': provider_data['client_id'],
        'redirect_uri': url_for('oauth2.oauth2_callback', provider=provider, _external=True),
        'response_type': 'code',
        'scope': ' '.join(provider_data['scopes']),
        'state': session['oauth2_state'],
    })
    return redirect(f"{provider_data['authorize_url']}?{qs}")





@bp.route('/callback/<provider>')
def oauth2_callback(provider):
    if session.get("uid"):
        return redirect(url_for('web.index'))

    p = _get_provider(provider)

    # Provider errors
    if 'error' in request.args:
        for k, v in request.args.items():
            if k.startswith('error'):
                flash(f'{k}: {v}', 'error')
        return redirect(url_for('web.index'))

    # CSRF
    state_in = request.args.get('state')
    if not state_in or state_in != session.get('oauth2_state'):
        abort(401)
    session.pop('oauth2_state', None)

    code = request.args.get('code')
    if not code:
        abort(401)

    # ---- Token exchange ----
    token_resp = requests.post(
        p['token_url'],
        data={
            'client_id': p['client_id'],
            'client_secret': p['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('oauth2.oauth2_callback', provider=provider, _external=True),
        },
        headers={'Accept': 'application/json'},
        timeout=10
    )
    if token_resp.status_code != 200:
        abort(401)

    token_json = token_resp.json()
    access_token = token_json.get('access_token')
    refresh_token = token_json.get('refresh_token')
    if not access_token:
        abort(401)

    expires_at = None
    expires_in_key = p.get('token_expires_in_key')
    if expires_in_key and token_json.get(expires_in_key):
        try:
            expires_at = utc_now() + timedelta(seconds=int(token_json[expires_in_key]))
        except Exception:
            expires_at = None

    # ---- Userinfo ----
    hdrs = {'Authorization': f'Bearer {access_token}', 'Accept': 'application/json'}

    ui_resp = requests.get(p['userinfo']['url'], headers=hdrs, timeout=10)
    if ui_resp.status_code != 200:
        abort(401)
    ui = ui_resp.json()

    get_id_fn = p['userinfo'].get('id')
    if not callable(get_id_fn):
        abort(500, description="Provider config missing callable 'userinfo.id'.")
    provider_user_id = str(get_id_fn(ui))  # normalize to str
    if not provider_user_id:
        abort(401, description="Could not obtain user ID from provider.")

    # Try inline email, then /user/emails
    email = ui.get('email')
    if not email:
        emails_url = p['userinfo'].get('emails_url')
        if emails_url:
            emails_resp = requests.get(emails_url, headers=hdrs, timeout=10)
            if emails_resp.status_code == 200:
                emails = emails_resp.json() or []
                primary_verified = next((e['email'] for e in emails if e.get('primary') and e.get('verified')), None)
                any_verified = next((e['email'] for e in emails if e.get('verified')), None)
                any_email = emails[0]['email'] if emails else None
                email = primary_verified or any_verified or any_email
    if email:
        email = email.strip().lower()

    # ---- Upsert link & user ----
    with SessionLocal() as db:
        oauth_link = db.execute(
            select(OAuthAccount).where(
                OAuthAccount.provider == provider,
                OAuthAccount.provider_user_id == provider_user_id
            )
        ).scalar_one_or_none()

        if oauth_link:
            oauth_link.access_token = access_token
            # If your model has these fields:
            if hasattr(oauth_link, 'refresh_token'):
                oauth_link.refresh_token = refresh_token
            if hasattr(oauth_link, 'expires_at'):
                oauth_link.expires_at = expires_at
            db.commit()

            session.clear()
            session["uid"] = oauth_link.user_id
            flash(f"Logged in with {provider.capitalize()}.", "success")
            return redirect(url_for('web.index'))

        # Not linked yet — find user by email if we have one
        user = None
        if email:
            user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        
        if user is None:
            user = User(
                email=email or f"{provider_user_id}@{provider}.invalid",
                password_hash=None,
            )
            db.add(user)
            try:
                db.commit()
                db.refresh(user)
            except IntegrityError:
                db.rollback()
                existing = db.execute(select(User).where(User.email == user.email)).scalar_one_or_none()
                if existing is None:
                    db.add(user)
                    db.commit()
                    db.refresh(user)
                else:
                    user = existing

        # Create OAuth link
        link = OAuthAccount(
            user_id=user.id,
            provider=provider,
            provider_user_id=provider_user_id,
            access_token=access_token,
        )
        if hasattr(link, 'refresh_token'):
            link.refresh_token = refresh_token
        if hasattr(link, 'expires_at'):
            link.expires_at = expires_at

        db.add(link)
        try:
            db.commit()
        except IntegrityError:
            db.rollback()
            # Unique constraint race; fetch and continue
            link = db.execute(
                select(OAuthAccount).where(
                    OAuthAccount.provider == provider,
                    OAuthAccount.provider_user_id == provider_user_id
                )
            ).scalar_one()

    # Log in
    session.clear()
    session["uid"] = user.id
    flash(f"Logged in with {provider.capitalize()}.", "success")
    return redirect(url_for('web.index'))




@bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('web.index'))
