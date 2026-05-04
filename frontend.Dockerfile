FROM ghcr.io/astral-sh/uv:python3.12-alpine

WORKDIR /app

# Copy CRM application (dashboard, approvals, eval, monitoring, architecture)
COPY crm/ ./

# Copy client shopping UI (served at /shop by FastAPI)
# app.py resolves client_dir as: core/app.py -> ../../client -> /client
COPY client/index.html /client/index.html
COPY client/src/ /client/src/

# Copy server evaluation module + config for running evals from CRM
COPY server/evaluation/ /server/evaluation/
COPY server/config/ /server/config/
COPY server/core/logger.py /server/core/logger.py

RUN uv sync --locked

# Add server to Python path so evaluation module is importable
ENV PYTHONPATH="/server:${PYTHONPATH}"

EXPOSE 8080

CMD ["uv", "run", "main.py"]
