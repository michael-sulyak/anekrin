makemigrations:
	aerich migrate

migrate:
	aerich upgrade

test:
	pytest app

bash:
	docker compose run --rm core bash

stats:
	docker compose run --rm core python3 scripts/stats.py
