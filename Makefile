makemigrations:
	aerich migrate

migrate:
	aerich upgrade

bash:
	docker-compose run --rm core bash

stats:
	docker-compose run --rm core python3 scripts/stats.py
