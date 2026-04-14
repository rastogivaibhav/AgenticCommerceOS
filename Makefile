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
	python -m pytest harness/python/tests/ -v

test-harness-python:
	python -m pytest harness/python/tests/ -v

test-harness-playwright-ui:
	cd apps/ops_ui_v2 && npm run test:e2e:ui

test-harness-playwright-integration:
	cd apps/ops_ui_v2 && npm run test:e2e:integration

test-harness-playwright-modules:
	cd apps/ops_ui_v2 && npm run test:e2e:modules

migrate:
	docker compose exec db psql -U acos -d acos -f /docker-entrypoint-initdb.d/01-schema.sql

.PHONY: all up down logs test migrate test-harness-python test-harness-playwright-ui test-harness-playwright-integration test-harness-playwright-modules
