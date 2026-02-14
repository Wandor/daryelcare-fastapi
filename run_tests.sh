#!/bin/bash

# ReadyKids CMA Test Runner Script

echo "=========================================="
echo "ReadyKids CMA FastAPI Test Suite"
echo "=========================================="
echo ""

# Check if we're in the right directory
if [ ! -f "requirements.txt" ]; then
    echo "Error: Please run this script from the project root directory"
    exit 1
fi

# Check if pytest is installed
if ! python -m pytest --version > /dev/null 2>&1; then
    echo "Installing test dependencies..."
    pip install -q pytest==8.3.4 pytest-asyncio==0.24.0 httpx==0.28.1
    echo "✅ Test dependencies installed"
    echo ""
fi

# Run tests based on argument
case "${1:-all}" in
    "all")
        echo "Running all tests..."
        python -m pytest tests/ -v
        ;;
    "utils")
        echo "Running service utility tests..."
        python -m pytest tests/test_service_utils.py -v
        ;;
    "api")
        echo "Running API route tests..."
        python -m pytest tests/test_api_routes.py -v
        ;;
    "db")
        echo "Running database integration tests..."
        python -m pytest tests/test_service_db.py -v
        ;;
    "transform")
        echo "Running dashboard transform tests..."
        python -m pytest tests/test_dashboard_transform.py -v
        ;;
    "coverage")
        echo "Running tests with coverage report..."
        if ! python -m pytest --version | grep -q "cov"; then
            echo "Installing pytest-cov..."
            pip install -q pytest-cov
        fi
        python -m pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
        echo ""
        echo "📊 Coverage report generated in htmlcov/index.html"
        ;;
    "quick")
        echo "Running quick smoke tests..."
        python -m pytest tests/ -x --tb=short
        ;;
    *)
        echo "Usage: ./run_tests.sh [all|utils|api|db|transform|coverage|quick]"
        echo ""
        echo "Options:"
        echo "  all        - Run all tests (default)"
        echo "  utils      - Run service utility tests only"
        echo "  api        - Run API route tests only"
        echo "  db         - Run database integration tests only"
        echo "  transform  - Run dashboard transform tests only"
        echo "  coverage   - Run tests with coverage report"
        echo "  quick      - Run quick smoke tests (stop on first failure)"
        exit 1
        ;;
esac

exit $?
