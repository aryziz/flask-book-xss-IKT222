FROM python:3.13-slim
WORKDIR /flask_books_xss
COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app \
    FLASK_APP=flask_books_xss:create_app \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=4000 \
    DATABASE_URL=sqlite:///instance/app.db \
    OAUTH_CLIENT_ID="Ov23liZnvt8W7MFvUZn4" \
    OAUTH_CLIENT_SECRET="834c8053cea1ef5ac03e7d138471b0455b60ca6c"
CMD ["python", "-m", "flask", "run"]
