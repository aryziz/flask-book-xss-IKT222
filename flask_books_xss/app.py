from dotenv import load_dotenv
from flask import g
from . import create_app

load_dotenv()
app = create_app()

def main():
    app.run(debug=True)
