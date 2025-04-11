"""
Configuration and fixtures for pytest tests.

This file contains shared fixtures and configuration that can be used
across multiple test files in the project.
"""

import os
import pytest
import requests


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
def session():
    """
    Create a session for better performance across tests.
    
    This reuses the same HTTP connection for multiple requests,
    which improves testing speed.
    """
    with requests.Session() as session:
        # Set reasonable timeout
        session.timeout = 10
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