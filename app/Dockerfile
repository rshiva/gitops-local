FROM python:3.10-slim AS builder
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

FROM python:3.10-slim AS runtime
RUN addgroup --system appgroup && adduser --system --ingroup appgroup appuser
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.10/site-packages /usr/local/lib/python3.10/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin
COPY . .
RUN chown -R appuser:appgroup /app
USER appuser
EXPOSE 8001
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8001"]
