.DEFAULT_GOAL := help

.PHONY: help setup test test-northstar ui-build compose-up compose-prod-up compose-down ecom-demo-up ecom-demo-down ecom-demo-verify ecom-demo-playwright smoke smoke-northstar runtime-check evidence-pack db-migrate db-migrate-sql

help:
	@echo "ACOS commands: setup | test | test-northstar | ui-build | compose-up | compose-prod-up | compose-down | ecom-demo-up | ecom-demo-verify | ecom-demo-playwright | ecom-demo-down | smoke | smoke-northstar | runtime-check | evidence-pack | db-migrate | db-migrate-sql"

setup:
	python -m pip install -r requirements-dev.txt
	cd apps/ops_ui_v2 && npm install

test:
	python -m pytest harness/python/tests/ -q

test-northstar:
	python -m pytest harness/python/tests/northstar -q

ui-build:
	cd apps/ops_ui_v2 && npm run build

compose-up:
	@test -f .env || cp .env.example .env
	docker compose up --build -d

compose-prod-up:
	@test -f .env.production || cp .env.production.example .env.production
	docker compose --env-file .env.production -f docker-compose.prod.yml up --build -d

compose-down:
	docker compose down || true
	docker compose -f docker-compose.prod.yml down || true
	docker compose --env-file .env.ecom-demo -f docker-compose.yml -f docker-compose.ecom-demo.yml down || true

ecom-demo-up:
	@test -f .env.ecom-demo || cp .env.ecom-demo.example .env.ecom-demo
	docker compose --env-file .env.ecom-demo -f docker-compose.yml -f docker-compose.ecom-demo.yml up --build -d

ecom-demo-down:
	docker compose --env-file .env.ecom-demo -f docker-compose.yml -f docker-compose.ecom-demo.yml down

ecom-demo-verify:
	@test -f .env.ecom-demo || cp .env.ecom-demo.example .env.ecom-demo
	python scripts/ecom_demo_verify.py --env-file .env.ecom-demo

ecom-demo-playwright:
	npm --prefix harness/playwright install
	npm --prefix harness/playwright run test:ecom-demo

smoke:
	python scripts/northstar_smoke.py

smoke-northstar:
	python scripts/northstar_smoke.py

runtime-check:
	python scripts/production_runtime_check.py

evidence-pack:
	python scripts/generate_ga_readiness_report.py


db-migrate:
	alembic upgrade head

db-migrate-sql:
	alembic upgrade head --sql

ui-load-check:
	PYTHONPATH=. python scripts/ui_load_check.py

acos-v2-demo:
	PYTHONPATH=. python scripts/acos_v2_demo_smoke.py

test-acos-v2:
	PYTHONPATH=. pytest -q harness/python/tests/northstar/test_acos_v2_estate.py
