# PhotoGeoView AI Integration Makefile
# Provides convenient commands for CI operations

.PHONY: help install ci ci-quick ci-full test lint format security performance clean setup-hooks

help:
	@echo "PhotoGeoView AI Integration - Available Commands:"
	@echo ""
	@echo "  install      - Install project dependencies"
	@echo "  ci           - Run standard CI checks"
	@echo "  ci-quick     - Run quick CI checks (code quality + unit tests)"
	@echo "  ci-full      - Run comprehensive CI checks"
	@echo "  test         - Run tests only"
	@echo "  lint         - Run code quality checks only"
	@echo "  format       - Auto-format code"
	@echo "  security     - Run security scans"
	@echo "  performance  - Run performance benchmarks"
	@echo "  setup-hooks  - Set up Git hooks"
	@echo "  clean        - Clean build artifacts"
	@echo ""

install:
	python -m pip install -e .[ci]

ci:
	python -m tools.ci.simulator run --checks code_quality test_runner --format both

ci-quick:
	python -m tools.ci.simulator run --checks code_quality test_runner --fail-fast

ci-full:
	python -m tools.ci.simulator run --checks all --format both

test:
	python -m tools.ci.simulator run --checks test_runner

lint:
	python -m tools.ci.simulator run --checks code_quality

format:
	python -m tools.ci.simulator run --checks code_quality --auto-fix

security:
	python -m tools.ci.simulator run --checks security_scanner

performance:
	python -m tools.ci.simulator run --checks performance_analyzer

setup-hooks:
	python -m tools.ci.simulator hook setup

clean:
	rm -rf build/ dist/ *.egg-info/
	rm -rf reports/ci-simulation/
	rm -rf temp/ci-simulation/
	rm -rf .pytest_cache/ .coverage htmlcov/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Development shortcuts
dev-setup: install setup-hooks
	@echo "Development environment set up successfully"

pre-commit: ci-quick
	@echo "Pre-commit checks completed"

pre-push: ci-full
	@echo "Pre-push checks completed"

# Build with CI
build: ci
	python -m build

# Deploy with full CI
deploy: ci-full
	python tools/create_deployment_package.py

# CI Simulator integration commands
ci-install:
	python -m tools.ci.simulator hook setup

ci-status:
	python -m tools.ci.simulator hook status

ci-uninstall:
	python -m tools.ci.simulator hook uninstall pre-commit

# Integration with existing build process
build-with-ci: ci-full
	python -m build
	python tools/create_deployment_package.py

# Production deployment with comprehensive checks
deploy-production: ci-full
	python tools/create_deployment_package.py --skip-tests
	@echo "Production deployment package created successfully"
