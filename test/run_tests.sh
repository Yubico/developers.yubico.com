#!/bin/bash

# Script to run the redirect tests against either production or local environments
# Usage: ./run_tests.sh [local|prod]

# Set default environment to production
ENV="prod"

# Check if environment parameter is provided
if [ "$1" = "local" ]; then
    ENV="local"
fi

echo "Setting up Python virtual environment..."
# Create virtual environment if it doesn't exist
if [ ! -d "env" ]; then
    python -m venv env
fi

# Activate virtual environment
source env/bin/activate

# Install dependencies
echo "Installing test dependencies..."
pip install -r requirements.txt

# Run tests based on environment
if [ "$ENV" = "local" ]; then
    echo "Running tests against local development server..."
    echo "Make sure your local server is running on localhost:8080!"
    TEST_DOMAIN=localhost:8080 TEST_PROTOCOL=http pytest test_redirects.py -v --html=report.html
else
    echo "Running tests against production server..."
    pytest test_redirects.py -v --html=report.html
fi

# Deactivate virtual environment
deactivate

echo "Tests completed."