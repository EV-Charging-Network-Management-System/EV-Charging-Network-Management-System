FROM node:22-alpine AS frontend
WORKDIR /app
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-slim
WORKDIR /app
COPY pyproject.toml ./
COPY backend ./backend
RUN pip install --no-cache-dir .
COPY alembic.ini ./
COPY database ./database
COPY deploy/start-demo.sh ./start-demo.sh
COPY --from=frontend /app/dist ./web
ENV FRONTEND_DIRECTORY=/app/web SECURE_COOKIES=true PYTHONUNBUFFERED=1
CMD ["sh", "./start-demo.sh"]
