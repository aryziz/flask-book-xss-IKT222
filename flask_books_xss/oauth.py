# flask_books_xss/oauth.py
import secrets
from urllib.parse import urlencode
import requests
from flask import Blueprint, current_app, abort, redirect, request, session, url_for, flash
from sqlalchemy import select
import secrets
from .db import SessionLocal
from .models.user import User

bp = Blueprint("oauth2", __name__)  # registered with url_prefix='/oauth' in create_app


def _get_provider(name: str) -> dict:
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
    # If already logged in, bounce home
    if session.get("uid"):
        return redirect(url_for('web.index'))

    provider_data = _get_provider(provider)

    # Provider-side errors
    if 'error' in request.args:
        for k, v in request.args.items():
            if k.startswith('error'):
                flash(f'{k}: {v}', 'error')
        return redirect(url_for('web.index'))

    # CSRF state check
    state_in = request.args.get('state')
    if not state_in or state_in != session.get('oauth2_state'):
        abort(401)

    code = request.args.get('code')
    if not code:
        abort(401)

    # Exchange code for token
    token_resp = requests.post(
        provider_data['token_url'],
        data={
            'client_id': provider_data['client_id'],
            'client_secret': provider_data['client_secret'],
            'code': code,
            'grant_type': 'authorization_code',
            'redirect_uri': url_for('oauth2.oauth2_callback', provider=provider, _external=True),
        },
        headers={'Accept': 'application/json'},
        timeout=10
    )
    if token_resp.status_code != 200:
        abort(401)
    oauth2_token = token_resp.json().get('access_token')
    if not oauth2_token:
        abort(401)

    # Fetch userinfo (email list for GitHub)
    ui_resp = requests.get(
        provider_data['userinfo']['url'],
        headers={
            'Authorization': f'Bearer {oauth2_token}',
            'Accept': 'application/json',
        },
        timeout=10
    )
    if ui_resp.status_code != 200:
        abort(401)

    # Provider config contains an extractor function for email
    email = provider_data['userinfo']['email'](ui_resp.json())
    if not email:
        abort(401, description="Could not obtain an email from provider.")

    # Upsert user using your SessionLocal

    db = SessionLocal()
    try:
        user = db.execute(select(User).where(User.email == email)).scalar_one_or_none()
        if user is None:
            user = User(email=email)  # user = User(email=email, username=email.split('@')[0])
            db.add(user)
            db.commit()
            db.refresh(user)

        # Use your existing session key—no Flask-Login required
        session.clear()
        session["uid"] = user.id
        flash("Logged in with GitHub.", "success")
    finally:
        db.close()
    return redirect(url_for('web.index'))



@bp.route('/logout')
def logout():
    session.clear()
    flash("Logged out.", "info")
    return redirect(url_for('web.index'))
