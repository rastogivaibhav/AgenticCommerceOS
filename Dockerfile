FROM python:3.11-slim

WORKDIR /app

# Create non-root user and group (FIX-08: HIGH-08)
RUN groupadd --system acos && useradd --system --gid acos --no-create-home acos

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app files with correct ownership
COPY --chown=acos:acos . .

# Drop to non-root before running
USER acos

ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

EXPOSE 8080

CMD ["uvicorn", "apps.shopper_api.main:app", "--host", "0.0.0.0", "--port", "8080"]
