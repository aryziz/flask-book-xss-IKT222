FROM python:3.13-slim
WORKDIR /flask_books_xss
COPY requirements.txt .
RUN python -m pip install --upgrade pip && pip install --no-cache-dir -r requirements.txt
COPY . .
ENV PYTHONPATH=/app \
    FLASK_APP=flask_books_xss:create_app \
    FLASK_RUN_HOST=0.0.0.0 \
    FLASK_RUN_PORT=5000 \
    DATABASE_URL=sqlite:///instance/app.db \
    VULNERABLE_MODE=true
CMD ["python", "-m", "flask", "run"]
