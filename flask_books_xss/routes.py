from flask import Blueprint, render_template, request, redirect, url_for, current_app
from .storage import add_book, list_books

web = Blueprint('web', __name__)

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
    
    if title and author and price:
        add_book(title, price, author)
    return redirect(url_for('web.index'))