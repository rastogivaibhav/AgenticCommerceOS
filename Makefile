.DEFAULT_GOAL := all

all: up

up:
	@test -f .env || (echo "ERROR: Copy .env.example to .env and fill in values"; exit 1)
	docker compose up --build -d

down:
	docker compose down

logs:
	docker compose logs -f

test:
	python -m pytest tests/ -v

migrate:
	docker compose exec db psql -U acos -d acos -f /docker-entrypoint-initdb.d/01-schema.sql

.PHONY: all up down logs test migrate
