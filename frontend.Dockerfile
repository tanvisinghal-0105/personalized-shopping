FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

# Copy CRM application (dashboard, approvals, eval, monitoring, architecture)
COPY crm/ ./

# Copy client shopping UI (served at /shop by FastAPI)
# app.py resolves client_dir as: core/app.py -> ../../client -> /client
COPY client/index.html /client/index.html
COPY client/src/ /client/src/

RUN uv sync --locked

EXPOSE 8080

CMD ["uv", "run", "main.py"]
