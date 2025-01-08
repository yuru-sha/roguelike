.PHONY: install run clean test lint format help

# Python実行環境の設定
PYTHON = poetry run python
PYTEST = poetry run pytest
BLACK = poetry run black
FLAKE8 = poetry run flake8
MYPY = poetry run mypy

# インストール
install:
	@echo "Installing dependencies..."
	poetry install

# 開発用インストール
install-dev: install
	@echo "Installing development dependencies..."
	poetry install --with dev

# ゲーム実行
run:
	@echo "Starting the game..."
	$(PYTHON) -m roguelike.main

# テスト実行
test:
	@echo "Running tests..."
	$(PYTEST)

# リンター実行
lint:
	@echo "Running linters..."
	$(FLAKE8) src/roguelike
	$(MYPY) src/roguelike

# コードフォーマット
format:
	@echo "Formatting code..."
	$(BLACK) src/roguelike

# キャッシュファイル削除
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name ".mypy_cache" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# ヘルプの表示
help:
	@echo "Available commands:"
	@echo "  make install     - Install dependencies"
	@echo "  make install-dev - Install development dependencies"
	@echo "  make run         - Run the game"
	@echo "  make test        - Run tests"
	@echo "  make lint        - Run linters"
	@echo "  make format      - Format code"
	@echo "  make clean       - Clean up generated files"
	@echo "  make help        - Show this help message" 