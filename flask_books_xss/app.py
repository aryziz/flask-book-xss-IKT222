from dotenv import load_dotenv
from . import create_app
from .storage import add_book, list_books

load_dotenv()
app = create_app()

def main():
    app.run(debug=True)
