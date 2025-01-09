.PHONY: install clean test lint format check all help dev build package assets watch

PYTHON := python3
POETRY := poetry
PACKAGE_NAME := roguelike

help:
	@echo "Available commands:"
	@echo "  make install    - Install dependencies"
	@echo "  make dev        - Install development dependencies"
	@echo "  make clean      - Clean temporary files"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Check code with linters"
	@echo "  make format     - Format code"
	@echo "  make check      - Run all checks"
	@echo "  make run        - Run the game"
	@echo "  make watch      - Run the game with auto-reload on file changes"
	@echo "  make build      - Build the package"
	@echo "  make package    - Create distribution package"
	@echo "  make assets     - Setup game assets"
	@echo "  make all        - Run all tasks"

install:
	$(POETRY) install --no-dev

dev:
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
	find . -type d -name "dist" -exec rm -rf {} +
	find . -type d -name "build" -exec rm -rf {} +
	find . -type f -name ".DS_Store" -delete

test:
	$(POETRY) run pytest tests/ --cov=$(PACKAGE_NAME) --cov-report=term-missing

lint:
	$(POETRY) run flake8 src/$(PACKAGE_NAME)
	$(POETRY) run mypy src/$(PACKAGE_NAME)

format:
	$(POETRY) run black src/$(PACKAGE_NAME) tests
	$(POETRY) run isort src/$(PACKAGE_NAME) tests

check: lint test

run:
	$(POETRY) run python -m $(PACKAGE_NAME)

watch:
	$(POETRY) run watchmedo auto-restart --directory=./src/$(PACKAGE_NAME) --pattern=*.py --recursive -- python -m $(PACKAGE_NAME)

build:
	$(POETRY) build

package: clean build
	$(POETRY) build -f sdist bdist_wheel

assets:
	mkdir -p data/assets
	cp -r src/$(PACKAGE_NAME)/data/assets/* data/assets/ 2>/dev/null || true
	@echo "Assets setup complete. If no files were copied, please check source assets location."

# Run all tasks in sequence
all: clean install format lint test build 