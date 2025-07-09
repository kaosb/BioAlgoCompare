# BioAlgoCompare Makefile
# Standardized development environment commands

.PHONY: help
help: ## Show this help message
	@echo 'BioAlgoCompare Development Commands'
	@echo '=================================='
	@echo ''
	@echo 'Usage: make [target]'
	@echo ''
	@echo 'Targets:'
	@awk 'BEGIN {FS = ":.*?## "} /^[a-zA-Z_-]+:.*?## / {printf "  %-20s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

# Environment Setup
.PHONY: setup
setup: ## Initial setup of development environment
	@echo "🔧 Setting up BioAlgoCompare development environment..."
	pip install --upgrade pip setuptools wheel
	pip install -r requirements.txt
	pip install -r requirements-dev.txt
	pip install -e .
	pre-commit install
	@echo "✅ Setup complete!"

.PHONY: install
install: ## Install project in editable mode
	pip install -e .

.PHONY: install-dev
install-dev: ## Install development dependencies
	pip install -r requirements-dev.txt
	pre-commit install

# Docker Commands
.PHONY: docker-build
docker-build: ## Build Docker images
	docker-compose build

.PHONY: docker-up
docker-up: ## Start development environment
	docker-compose up -d bioalgo-dev

.PHONY: docker-down
docker-down: ## Stop all containers
	docker-compose down

.PHONY: docker-shell
docker-shell: ## Open shell in development container
	docker-compose exec bioalgo-dev /bin/bash

.PHONY: docker-jupyter
docker-jupyter: ## Start Jupyter Lab server
	docker-compose up -d bioalgo-jupyter
	@echo "📓 Jupyter Lab available at http://localhost:8888 (token: bioalgo2024)"

.PHONY: docker-clean
docker-clean: ## Clean Docker resources
	docker-compose down -v
	docker system prune -f

# Quality Checks
.PHONY: quality
quality: ## Run all quality checks
	python scripts/quality/quality_gates.py

.PHONY: quality-required
quality-required: ## Run only required quality checks
	python scripts/quality/quality_gates.py --required-only

.PHONY: format
format: ## Format code with ruff
	ruff format .

.PHONY: lint
lint: ## Lint code with ruff
	ruff check . --fix

.PHONY: type-check
type-check: ## Run type checking with mypy
	mypy algorithms/ utils/ --ignore-missing-imports

.PHONY: security
security: ## Run security checks with bandit
	bandit -r algorithms/ utils/ scripts/ -ll

# Testing
.PHONY: test
test: ## Run all tests
	pytest -v

.PHONY: test-fast
test-fast: ## Run fast tests only
	pytest -v -k "not slow"

.PHONY: test-coverage
test-coverage: ## Run tests with coverage report
	pytest --cov=algorithms --cov=problems --cov=utils --cov-report=html --cov-report=term

.PHONY: test-parallel
test-parallel: ## Run tests in parallel
	pytest -v -n auto

.PHONY: test-failed
test-failed: ## Re-run failed tests
	pytest -v --lf

# Running Algorithms
.PHONY: run-hoa
run-hoa: ## Run HOA algorithm example
	python scripts/cli/main.py run --algorithm hoa --instance E-n22-k4 --iterations 100

.PHONY: run-benchmark
run-benchmark: ## Run small benchmark
	python scripts/cli/main.py benchmark --run-benchmark \
		--instances "E-n22-k4,P-n16-k8" \
		--algorithms "hoa,foa,egto" \
		--runs 5

# Documentation
.PHONY: docs
docs: ## Build documentation
	cd docs && make html
	@echo "📚 Documentation available at docs/_build/html/index.html"

.PHONY: docs-serve
docs-serve: docs ## Build and serve documentation
	cd docs/_build/html && python -m http.server 8080

# Cleaning
.PHONY: clean
clean: ## Clean build artifacts
	find . -type f -name '*.pyc' -delete
	find . -type d -name '__pycache__' -delete
	find . -type d -name '.pytest_cache' -exec rm -rf {} +
	find . -type d -name '.ruff_cache' -exec rm -rf {} +
	find . -type d -name '.mypy_cache' -exec rm -rf {} +
	find . -type d -name '*.egg-info' -exec rm -rf {} +
	rm -rf build/ dist/ htmlcov/ .coverage coverage.xml

.PHONY: clean-results
clean-results: ## Clean result files
	find results/ -name "*.csv" -mtime +7 -delete
	find results/ -name "*.json" -mtime +7 -delete

.PHONY: clean-all
clean-all: clean clean-results ## Clean everything
	rm -rf .tox/
	rm -rf docs/_build/

# Development Workflow
.PHONY: dev-check
dev-check: format lint test-fast ## Quick development check

.PHONY: pre-commit
pre-commit: ## Run pre-commit on all files
	pre-commit run --all-files

.PHONY: update-deps
update-deps: ## Update dependencies
	pip-compile requirements.in -o requirements.txt
	pip-compile requirements-dev.in -o requirements-dev.txt

# Utility Commands
.PHONY: shell
shell: ## Open IPython shell with project context
	ipython -i -c "from algorithms import *; from problems.vrp import VRPProblem; print('BioAlgoCompare shell ready!')"

.PHONY: stats
stats: ## Show code statistics
	@echo "📊 Code Statistics:"
	@echo "Lines of code:"
	@find algorithms problems utils scripts -name "*.py" -type f | xargs wc -l | tail -1
	@echo ""
	@echo "Number of files:"
	@find algorithms problems utils scripts -name "*.py" -type f | wc -l
	@echo ""
	@echo "Number of algorithms:"
	@ls algorithms/*.py | grep -v -E "(base|__init__|legacy)" | wc -l

.PHONY: todo
todo: ## Show all TODO items
	@grep -r "TODO" algorithms/ problems/ utils/ scripts/ --include="*.py" | grep -v "TODO_.*_COMPLETED"

# Git Hooks
.PHONY: install-hooks
install-hooks: ## Install git hooks
	pre-commit install
	python scripts/quality/quality_gates.py --install-hook

# Environment Info
.PHONY: info
info: ## Show environment information
	@echo "🔍 BioAlgoCompare Environment Info"
	@echo "================================="
	@echo "Python: $$(python --version)"
	@echo "Pip: $$(pip --version)"
	@echo "Git: $$(git --version)"
	@echo "Current branch: $$(git branch --show-current)"
	@echo "Working directory: $$(pwd)"
	@echo ""
	@echo "Key dependencies:"
	@pip list | grep -E "(numpy|pandas|matplotlib|ruff|pytest)"

# Default target
.DEFAULT_GOAL := help