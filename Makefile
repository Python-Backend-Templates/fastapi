PROJECT_NAME=fastapi-n-postgres-template

localup:
	docker compose -f docker-compose.local.yml up --remove-orphans
localbuild:
	docker compose -f docker-compose.local.yml build --no-cache
developup:
	docker compose -f docker-compose.develop.yml up --remove-orphans
developbuild:
	docker compose -f docker-compose.develop.yml build --no-cache
test:
	docker exec -it $(PROJECT_NAME)-asgi pytest .
flake8:
	docker exec -it $(PROJECT_NAME)-asgi flake8 .
mypy:
	docker exec -it $(PROJECT_NAME)-asgi mypy .
black:
	docker exec -it $(PROJECT_NAME)-asgi black .
isort:
	docker exec -it $(PROJECT_NAME)-asgi isort . --profile black --filter-files
makemigrations:
	docker exec -it $(PROJECT_NAME)-asgi alembic revision -m "$(MESSAGE)"
migrate:
	docker exec -it $(PROJECT_NAME)-asgi alembic upgrade head
