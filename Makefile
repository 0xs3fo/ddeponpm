# Makefile for DEPONPM

.PHONY: install test clean help

# Default target
help:
	@echo "DEPONPM - NPM Dependency Checker Tool"
	@echo "====================================="
	@echo ""
	@echo "Available targets:"
	@echo "  install    - Install dependencies"
	@echo "  test       - Run tests"
	@echo "  clean      - Clean up temporary files"
	@echo "  help       - Show this help message"
	@echo ""
	@echo "Usage:"
	@echo "  make install"
	@echo "  python3 deponpm.py ./package.json"

# Install dependencies
install:
	pip3 install -r requirements.txt
	chmod +x deponpm.sh

# Run tests
test:
	python3 deponpm.py --help
	python3 deponpm.py test-package.json

# Clean up
clean:
	find . -type f -name "*.pyc" -delete
	find . -type d -name "__pycache__" -delete
