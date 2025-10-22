# User Authentication

## Running manually
### Requirements
* Python 3.11 or 3.12
 
1. Create & activate virtual environment
```bash
python -m venv .venv
# Windows
.\.venv\Scripts\activate.bat

# Linux/macOS
source .venv/bin/activate
```

2. Install dependencies

```bash
pip install -r requirements.txt
```

1. Create .env file like `example.env`
2. Run project

```bash
flask --app flask_books_xss run
```

## Running in Docker

1. Build

```bash
docker build -t books-xss .
```

2. Run (with docker compose)

```bash
docker compose up
```
-> Access page on http://localhost:4000