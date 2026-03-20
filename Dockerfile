FROM node:20-slim AS ui-build

WORKDIR /ui

COPY apps/ops_ui_v2/package.json apps/ops_ui_v2/package-lock.json ./
RUN npm install

COPY apps/ops_ui_v2 ./
RUN npm run build


FROM python:3.11-slim

WORKDIR /app

# Create non-root user and group.
RUN groupadd --system acos && useradd --system --gid acos --no-create-home acos

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --chown=acos:acos . .
COPY --from=ui-build --chown=acos:acos /ui/dist ./apps/ops_api/ui

USER acos

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["uvicorn", "apps.shopper_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
