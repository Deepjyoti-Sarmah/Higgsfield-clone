# syntax=docker/dockerfile:1
# One image for both Railway services: APP_ROLE=api (default) or APP_ROLE=worker.

FROM node:24-slim AS web
WORKDIR /repo/apps/web
COPY apps/web/package.json apps/web/package-lock.json ./
RUN npm ci
COPY packages/contracts /repo/packages/contracts
COPY apps/web/ ./
RUN npm run gen:api && npm run build

FROM python:3.12-slim AS app
COPY --from=ghcr.io/astral-sh/uv:0.9 /uv /usr/local/bin/uv
WORKDIR /app
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PROJECT_ENVIRONMENT=/app/.venv UV_PYTHON_DOWNLOADS=never
COPY apps/api/pyproject.toml apps/api/uv.lock apps/api/.python-version ./
RUN uv sync --frozen --no-dev --no-install-project
COPY apps/api/ ./
COPY --from=web /repo/apps/web/dist /app/static
ENV PATH="/app/.venv/bin:$PATH" STATIC_DIR=/app/static PORT=8000 APP_ROLE=api
EXPOSE 8000
CMD ["sh", "entrypoint.sh"]
