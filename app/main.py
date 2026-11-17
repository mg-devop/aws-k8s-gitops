import os
import psycopg2
from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from prometheus_client import Counter, generate_latest

app = FastAPI()
REQUEST_COUNT = Counter("app_api_requests_total", "Total requests to /api")

def get_conn():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres-svc"),
        dbname=os.getenv("DB_NAME", "appdb"),
        user=os.getenv("DB_USER", "appuser"),
        password=os.getenv("DB_PASSWORD", "AppUserPass2026!"),
        connect_timeout=3,
    )

@app.on_event("startup")
def init_db():
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS audit_log (
                id SERIAL PRIMARY KEY,
                event TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
        """)
        conn.commit()

@app.get("/api")
def read_write_db():
    REQUEST_COUNT.inc()
    with get_conn() as conn, conn.cursor() as cur:
        cur.execute(
            "INSERT INTO audit_log (event) VALUES (%s) RETURNING id, created_at;",
            ("ArgoCD + ECR API hit",),
        )
        row = cur.fetchone()
        cur.execute("SELECT COUNT(*) FROM audit_log;")
        total = cur.fetchone()[0]
        conn.commit()
    return {
        "status": "connected",
        "database": "PostgreSQL on AWS EBS (gp3)",
        "inserted_id": row[0],
        "timestamp": str(row[1]),
        "total_persisted_records": total,
    }

@app.get("/metrics", response_class=PlainTextResponse)
def metrics():
    return generate_latest()
