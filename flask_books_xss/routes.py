from flask import Blueprint, render_template, request, redirect, url_for, current_app, flash
from .storage import add_book, list_books
from bleach.sanitizer import Cleaner
import unicodedata, re
from decimal import Decimal, InvalidOperation

web = Blueprint('web', __name__)

_ALLOWED_TAGS = ["b", "i", "em", "strong", "a", "style", "p"]
_ALLOWED_ATTRS = {"a" : ["href", "title", "rel"]}
_HTML_CLEANER  = Cleaner(
    tags=_ALLOWED_TAGS,
    attributes=_ALLOWED_ATTRS,
    protocols=["http", "https"],
    strip=True,
    strip_comments=True
)

def sanitize_html(value: str, *, max_len: int=500) -> str:
    val = unicodedata.normalize("NFC", value or "").strip()
    val = _HTML_CLEANER.clean(val)
    val = re.sub(r"\s+", " ", value)
    return value[:max_len]


@web.get('/')
def index():
    return render_template('index.html', books=list_books())

@web.context_processor
def inject_flags():
    return {"vulnerable": current_app.config["VULNERABLE_MODE"]}

@web.post('/list')
def list_book():
    
    title = request.form.get('title', '')
    author = request.form.get('seller', '')
    price = request.form.get('price', '')
    
    if not current_app.config["VULNERABLE_MODE"]:
        title = sanitize_html(title, max_len=120)
        author = sanitize_html(author, max_len=120)
        
        try:
            price = int(price)
            if price < 0 or price > 100000:
                raise ValueError("Price out of range")
        except (InvalidOperation, ValueError):
            flash("Invalid price.", "error")
            return redirect(url_for("web.index"))
    
    if title and author and price:
        add_book(title, price, author)
    return redirect(url_for('web.index'))