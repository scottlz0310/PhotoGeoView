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
	python -m tools.ci.simulator run code_quality test_runner --format both

ci-quick:
	python -m tools.ci.simulator run code_quality test_runner --fail-fast

ci-full:
	python -m tools.ci.simulator run --all --format both --python-versions 3.9 3.10 3.11

test:
	python -m tools.ci.simulator run test_runner

lint:
	python -m tools.ci.simulator run code_quality

format:
	python -m tools.ci.simulator run code_quality --auto-fix

security:
	python -m tools.ci.simulator run security_scanner

performance:
	python -m tools.ci.simulator run performance_analyzer

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

# Validate CI integration
validate-ci:
	python scripts/validate_ci_integration.py
	@echo "CI integration validation completed"

# Check CI integration status
ci-status:
	python tools/ci_integration.py validate
	@echo "CI integration status check completed"

# Generate CI integration report
ci-report:
	python tools/ci_integration.py report --output reports/ci-integration-report.md
	@echo "CI integration report generated"

# Set up CI integration
setup-ci:
	python scripts/setup_ci_integration.py
	@echo "CI integration setup completed"

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

# CI Simulator integration with existing workflows
ci-integration-check:
	python -m tools.ci.simulator run code_quality test_runner security_scanner --format json --output-dir reports/ci-integration
	@echo "CI integration check completed"

# Validate CI simulator integration
validate-ci-integration:
	python scripts/validate_ci_integration.py
	python -m tools.ci.simulator run --all --format both --timeout 300
	@echo "CI integration validation completed"

# Setup development environment with CI integration
dev-setup-full: install setup-hooks ci-integration-check
	@echo "Full development environment with CI integration set up successfully"
