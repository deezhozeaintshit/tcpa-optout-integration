web: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers ${WEB_CONCURRENCY:-2}
release: echo "Migrations and table creation handled by app lifespan"
