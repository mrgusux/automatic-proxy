.PHONY: install install-dev run test lint format clean docker

install:
    python -m pip install --upgrade pip
    pip install -r requirements.txt

install-dev:
    python -m pip install --upgrade pip
    pip install -r requirements.txt
    pip install -e ".[dev]"

run:
    python -m src.main run --log-level INFO

test:
    pytest -q

lint:
    ruff check src tests
    mypy src

format:
    ruff format src tests
    ruff check --fix src tests

clean:
    rm -rf .pytest_cache .ruff_cache .mypy_cache
    find . -type d -name __pycache__ -exec rm -rf {} +

docker:
    docker compose -f docker/docker-compose.yml up --build
