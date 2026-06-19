import time

from fastapi import FastAPI, Response
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from database.db import create_tables
from metrics import task_request_duration_seconds
from routes.user import user_routes

app = FastAPI()


class MetricsMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        duration = time.perf_counter() - start
        task_request_duration_seconds.labels(
            method=request.method,
            path=request.url.path,
            status_code=str(response.status_code),
        ).observe(duration)
        return response


app.add_middleware(MetricsMiddleware)
app.include_router(user_routes, prefix="/user")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.on_event("startup")
def startup_db_client():
    create_tables()
