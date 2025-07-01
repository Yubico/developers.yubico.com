#!/bin/bash

# Script to run the redirect tests against production, staging, or local environments
# Usage: ./run_tests.sh [local|stage|prod] [--with-token]

# Set default environment to production
ENV="prod"
USE_TOKEN=false

# Check if environment parameter is provided
if [ "$1" = "local" ]; then
    ENV="local"
elif [ "$1" = "stage" ]; then
    ENV="stage"
elif [ "$1" = "prod" ]; then
    ENV="prod"
else
    echo "Unknown environment '$1'. Using production as default."
fi

# Check if --with-token flag is provided
if [ "$2" = "--with-token" ] || [ "$3" = "--with-token" ]; then
    USE_TOKEN=true
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

# Special handling for staging environment
if [ "$ENV" = "stage" ]; then
    echo "Preparing to test staging environment..."
    
    # Check if ID_TOKEN is already set
    if [ -z "$ID_TOKEN" ]; then
        echo "No ID_TOKEN environment variable found."
        
        if [ "$USE_TOKEN" = "true" ]; then
            echo "Generating ID token for staging environment..."
            
            # Check if gcloud is available
            if ! command -v gcloud &> /dev/null; then
                echo "Error: gcloud command not found. Cannot generate ID token."
                echo "Please install Google Cloud SDK or provide a token manually."
                exit 1
            fi
            
            export ID_TOKEN=$(gcloud auth print-identity-token \
                --impersonate-service-account=local-site-tester@stage-developers-812464.iam.gserviceaccount.com \
                --audiences=746478293890-vm3m0ii6ppqg7b66qme1fs277l8u37hj.apps.googleusercontent.com \
                --include-email)
            
            if [ -z "$ID_TOKEN" ]; then
                echo "Error: Failed to generate ID token."
                exit 1
            fi
            
            echo "ID token generated successfully."
            echo "Token length: ${#ID_TOKEN}"
            echo "Token preview: ${ID_TOKEN:0:20}..."
        else
            echo "WARNING: No ID_TOKEN and --with-token not specified."
            echo "Tests against staging will likely fail due to missing authentication."
            echo "To automatically generate a token, use: ./run_tests.sh stage --with-token"
        fi
    else
        echo "Using existing ID_TOKEN from environment."
        
        # Check if token is valid if token_utils.py exists
        if [ -f "token_utils.py" ]; then
            echo "Checking token validity..."
            python -c "from token_utils import check_id_token; is_valid, msg = check_id_token(); print(f'Token valid: {is_valid}'); print(msg); exit(0 if is_valid else 1)" || {
                echo "ERROR: Token is invalid or expired. Please generate a new token."
                exit 1
            }
        fi
    fi
fi

# Run tests based on environment
if [ "$ENV" = "local" ]; then
    echo "Running tests against local development server..."
    echo "Make sure your local server is running on localhost:8080!"
    TEST_DOMAIN=localhost:8080 TEST_PROTOCOL=http pytest test_redirects.py test_releases_redirects.py -v --html=report.html
elif [ "$ENV" = "stage" ]; then
    echo "Running tests against staging server..."
    TEST_DOMAIN=developers.stage.yubico.com TEST_PROTOCOL=https pytest test_redirects.py test_releases_redirects.py -v --html=report.html
else
    echo "Running tests against production server..."
    pytest test_redirects.py test_releases_redirects.py -v --html=report.html
fi

# Save the exit code
EXIT_CODE=$?

# Deactivate virtual environment
deactivate

# Exit with the same code as pytest
echo "Tests completed with exit code: $EXIT_CODE"
exit $EXIT_CODE
