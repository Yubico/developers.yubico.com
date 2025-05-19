"""
Configuration and fixtures for pytest tests.

This file contains shared fixtures and configuration that can be used
across multiple test files in the project.
"""

import os
import sys
import pytest
import requests
from token_utils import check_id_token


# Check for staging environment and token validity early
def check_staging_token():
    """
    Check if we're testing staging and if a valid token is available.
    Exit early if running against staging without a valid token.
    """
    domain = os.environ.get('TEST_DOMAIN', 'developers.yubico.com')
    
    # Only check for staging environment
    if 'stage.yubico.com' in domain:
        print("\n=== Checking staging environment authentication ===")
        id_token = os.environ.get('ID_TOKEN')
        
        if not id_token:
            print("ERROR: No ID_TOKEN environment variable found for staging environment.")
            print("Tests against staging will fail due to IAP authentication.")
            print("Run 'source ./get_token.sh' to generate a token.")
            print("Exiting test suite to avoid running tests that will certainly fail.")
            sys.exit(1)
        
        # Check token validity
        is_valid, message = check_id_token()
        if not is_valid:
            print(f"ERROR: ID token invalid or expired: {message}")
            print("Tests against staging will fail with this token.")
            print("Run 'source ./get_token.sh' to generate a new token.")
            print("Exiting test suite to avoid running tests that will certainly fail.")
            sys.exit(1)
        
        print(f"✅ Using ID_TOKEN for authentication: {message}")
        
    return True


# Run the check early when this module is imported
check_staging_token()


@pytest.fixture(scope="session")
def base_url():
    """
    Get the base URL for testing.
    
    This allows switching between production and local development
    environments through environment variables.
    """
    domain = os.environ.get('TEST_DOMAIN', 'developers.yubico.com')
    protocol = os.environ.get('TEST_PROTOCOL', 'https')
    return f"{protocol}://{domain}"


@pytest.fixture(scope="session")
def eol_redirect_target():
    """
    Get the EOL policy page URL that EOL projects should redirect to.
    """
    return os.environ.get(
        'TEST_EOL_TARGET',
        'https://www.yubico.com/support/terms-conditions/yubico-end-of-life-policy/eol-products/'
    )


@pytest.fixture(scope="module")
def session(base_url):
    """
    Create a session for better performance across tests.
    
    This reuses the same HTTP connection for multiple requests,
    which improves testing speed. Also applies authorization headers
    if ID_TOKEN environment variable is set (used for staging environment).
    """
    with requests.Session() as session:
        # Set reasonable timeout
        session.timeout = 10

        # Check if we're testing the staging environment
        if 'stage.yubico.com' in base_url:
            # Add token to session headers
            id_token = os.environ.get('ID_TOKEN')
            session.headers.update({
                'Authorization': f'Bearer {id_token}'
            })
            print(f"Added authorization header to requests")
        else:
            print(f"Testing environment: {base_url} (no authentication required)")

        yield session


@pytest.fixture(scope="function")
def verify_redirect():
    """
    Fixture that returns a function to verify redirects.
    
    This makes test assertions more readable and provides consistent
    error messages.
    """
    def _verify_redirect(session, url, expected_location):
        """
        Verify that a URL redirects to the expected location.
        
        Args:
            session: requests.Session to use for the request
            url: URL to test
            expected_location: Expected redirect target URL
            
        Returns:
            tuple: (success, status_code, actual_location, error_message)
        """
        try:
            # Follow all redirects
            response = session.get(url, allow_redirects=True)
            
            # Get the final URL after all redirects
            final_url = response.url
            
            # Debug output
            print(f"Testing redirect: {url} → {final_url}")
            print(f"Expected: {expected_location}")
            
            # Check for Google login redirect
            if 'accounts.google.com' in final_url:
                return False, response.status_code, final_url, "Redirected to Google login page. Authentication failed."
            
            # Normalize the expected location and final URL for comparison
            # This handles minor differences like trailing slashes
            expected_norm = expected_location.rstrip('/')
            final_norm = final_url.rstrip('/')
            
            if final_norm == expected_norm:
                return True, response.status_code, final_url, ""
            else:
                redirect_chain = [h.headers.get('Location', '') for h in response.history]
                redirect_info = " -> ".join([url] + redirect_chain + [final_url])
                return False, response.status_code, final_url, f"Expected final redirect to {expected_location}, got {final_url}\nRedirect chain: {redirect_info}"
        except Exception as e:
            return False, 0, "", str(e)
    return _verify_redirect