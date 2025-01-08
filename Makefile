.PHONY: install clean test lint format check all help

PYTHON := python3
POETRY := poetry

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make clean      - Clean temporary files"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Check code with linters"
	@echo "  make format     - Format code"
	@echo "  make check      - Run all checks"
	@echo "  make run        - Run the game"
	@echo "  make all        - Run all tasks"

install:
	$(POETRY) install

clean:
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.py[cod]" -delete
	find . -type f -name "*.so" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name "*.egg" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".coverage" -delete
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name ".DS_Store" -delete

test:
	$(POETRY) run pytest tests/

lint:
	$(POETRY) run flake8 src/roguelike
	$(POETRY) run mypy src/roguelike

format:
	$(POETRY) run black src/roguelike tests
	$(POETRY) run isort src/roguelike tests

check: lint test

run:
	$(POETRY) run python src/roguelike/main.py

setup-assets:
	mkdir -p data/assets
	cp -r src/roguelike/data/assets/* data/assets/ || true
	@echo "Note: If no assets were copied, please ensure the source assets are in the correct location."

# Run all tasks in sequence
all: clean install format lint test 