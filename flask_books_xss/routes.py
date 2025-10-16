# routes.py
from __future__ import annotations

import re
import unicodedata
from decimal import InvalidOperation

from bleach.sanitizer import Cleaner
from flask import (
    Blueprint,
    flash,
    g,
    redirect,
    render_template,
    request,
    url_for,
)

from .listings import create_listing, list_public, list_mine

web = Blueprint("web", __name__)

# ---- HTML sanitizer (corrected) ----
_ALLOWED_TAGS = ["b", "i", "em", "strong", "a", "p"]
_ALLOWED_ATTRS = {"a": ["href", "title", "rel"]}
_HTML_CLEANER = Cleaner(
    tags=_ALLOWED_TAGS,
    attributes=_ALLOWED_ATTRS,
    protocols=["http", "https"],
    strip=True,
    strip_comments=True,
)

def sanitize_html(value: str, *, max_len: int = 500) -> str:
    val = unicodedata.normalize("NFC", value or "").strip()
    val = _HTML_CLEANER.clean(val)
    val = re.sub(r"\s+", " ", val)
    return val[:max_len]

@web.context_processor
def inject_flags():
    return {
        "user": g.get("user"),
    }

# ---------- Pages ----------
@web.get("/")
def index():
    return render_template("index.html", books=list_public())

@web.post("/list")
def list_book():
    if not g.user:
        flash("Please log in to create a listing.", "error")
        return redirect(url_for("auth.login"))

    title = request.form.get("title", "")
    price_raw = request.form.get("price", "")
    description = request.form.get("description", "")

    title = sanitize_html(title, max_len=120)
    description = sanitize_html(description, max_len=2000)
    try:
        price = int(price_raw)
        if price < 0 or price > 100_000:
            raise ValueError("Price out of range")
    except (InvalidOperation, ValueError):
        flash("Invalid price.", "error")
        return redirect(url_for("web.index"))

    if not title:
        flash("Title is required.", "error")
        return redirect(url_for("web.index"))

    create_listing(user_id=g.user.id, title=title, price=price, description=description or None)
    return redirect(url_for("web.index"))

@web.get("/mine")
def my_listings():
    if not g.user:
        return redirect(url_for("auth.login"))
    rows = list_mine(g.user.id)
    return render_template("my_listings.html", rows=rows)
