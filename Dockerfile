# Stage 1: build the React frontend (vite 8 needs node >= 20.19)
FROM node:22-alpine AS web-build
WORKDIR /web
COPY web/package.json web/package-lock.json ./
RUN npm ci
COPY web/ ./
RUN npm run build

# Stage 2: FastAPI serves the API and the built frontend from web/dist
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY core/ ./core/
COPY api/ ./api/
# api/main.py resolves the frontend at <repo root>/web/dist
COPY --from=web-build /web/dist ./web/dist/

# Render injects PORT; default to 8000 for local docker runs
CMD uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}
