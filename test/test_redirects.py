"""
Tests for redirect functionality on the Yubico developers website.

This module tests that:
1. EOL projects redirect to the proper EOL policy page
2. Standard redirects work as expected

Usage:
    pytest test_redirects.py -v

To test against local development:
    TEST_DOMAIN=localhost:8080 TEST_PROTOCOL=http pytest test_redirects.py -v
    
To test against staging using ID_TOKEN:
    ID_TOKEN=your_token_here TEST_DOMAIN=developers.stage.yubico.com TEST_PROTOCOL=https pytest test_redirects.py -v
"""

import pytest
import os
import requests
from urllib.parse import urljoin


# List of EOL projects to test
EOL_PROJECTS = [
    "yubico-val",
    "yubico-pam",
    "u2fval-client-php",
    "yubikey-ksm",
    "u2fval-client-python",
    "python-u2flib-server",
    "python-u2flib-host",
    "libu2f-host",
    "yubico-c-client",
    "php-u2flib-server",
    "java-u2flib-server",
    "php-yubico",
    "yubico-dotnet-client",
    "yubico-perl-client",
    "yubiclip-android",
    "python-yubicommon",
    "yubikey-neo-demo",
    "yubiyey-piv-manager",
    "yubix-vm",
    "wordpress-u2f",
    "ifd-yubico",
    "yubico-windows-auth",
    "yubix",
    "yubiadmin",
    "ykneo-ccid-tools",
    "yubico-dbus-notifier",
    "yubico-bitcoin-python",
    "yubikey-salesforce-client",
    "yubico-bitcoin-java",
    "ykneo-curves",
    "yubiauth",
    "rlm_yubico",
    "yubico-shibboleth-idp-multifactor-login-handler",
    "Yubiotp-android",
    "yubikey-neo-manager",
    "libykneomgr"
]

def verify_redirect(session, url, expected_final_url, max_redirects=5):
    """
    Verify a URL redirects to the expected final destination.
    
    Args:
        session: Session object for making requests
        url: URL to test
        expected_final_url: Expected final URL after all redirects
        max_redirects: Maximum number of redirects to follow
        
    Returns:
        tuple: (success, status_code, actual_location, error_msg)
    """
    try:
        # Start with the initial URL
        current_url = url
        redirect_chain = []
        status_code = None
        
        # Follow redirects manually
        for _ in range(max_redirects):
            print(f"Testing redirect: {current_url}")
            response = session.get(current_url, allow_redirects=False, timeout=10)
            status_code = response.status_code
            
            # If not a redirect status code, we've reached the end
            if status_code not in (301, 302, 303, 307, 308):
                break
                
            # Get the next URL and add it to the chain
            next_url = response.headers.get('Location', '')
            redirect_chain.append(f"{current_url} → {next_url}")
            
            # If we've reached the expected URL, we're done
            if next_url == expected_final_url:
                return True, status_code, next_url, "Success"
                
            # Move to the next URL
            current_url = next_url
        
        # If we exited the loop without finding the expected URL
        print(f"Expected: {expected_final_url}")
        
        # Format the redirect chain for error reporting
        chain_str = "\n".join(redirect_chain)
        return False, status_code, current_url, f"Expected final redirect to {expected_final_url}, got {current_url}\nRedirect chain: {chain_str}"
        
    except Exception as e:
        return False, 0, "", f"Error: {str(e)}"

class TestEolRedirects:
    """Test that EOL project URLs redirect to the EOL policy page."""
    
    @pytest.mark.parametrize("project", EOL_PROJECTS)
    def test_eol_project_base(self, session, base_url, eol_redirect_target, verify_redirect, project):
        """Test that base EOL project URLs redirect correctly."""
        project_url = f"{base_url}/{project}"
        expected_location = f"{eol_redirect_target}?project={project}"
        
        success, status_code, actual_location, error_msg = verify_redirect(
            session, project_url, expected_location)
        
        assert success, f"Failed redirect for {project_url}: {error_msg}"
    
    @pytest.mark.parametrize("project", EOL_PROJECTS)
    def test_eol_project_subpath(self, session, base_url, eol_redirect_target, verify_redirect, project):
        """Test that EOL project subpaths also redirect correctly."""
        subpath_url = f"{base_url}/{project}/docs"
        expected_location = f"{eol_redirect_target}?project={project}"
        
        success, status_code, actual_location, error_msg = verify_redirect(
            session, subpath_url, expected_location)
            
        assert success, f"Failed redirect for {subpath_url}: {error_msg}"


class TestStandardRedirects:
    """Test standard redirect functionality on the website."""

    def test_fido2_redirects(self, session, base_url, verify_redirect):
        """Test FIDO2 redirects with browser-like headers."""
        
        # Set browser-like headers for more reliable testing
        original_headers = session.headers.copy()
        session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        })
        
        try:
            redirects = {
                'fido2': f"{base_url}/WebAuthn/",
                'fido2/': f"{base_url}/WebAuthn/",
                'FIDO2': f"{base_url}/WebAuthn/",
                'FIDO2/': f"{base_url}/WebAuthn/",
            }
            
            for path, target in redirects.items():
                url = urljoin(base_url + '/', path)
                
                success, status_code, actual_location, error_msg = verify_redirect(
                    session, url, target)
                    
                assert success, f"Failed redirect for {url}: {error_msg}"
        finally:
            # Restore original headers
            session.headers = original_headers    
            
    def test_renamed_urls(self, session, base_url, verify_redirect):
        """Test redirects for renamed URLs."""
        redirects = {
            'yubikey5ci': f"{base_url}/Mobile/",
            'yubioath-desktop': f"{base_url}/yubioath-flutter/",
        }
        
        for path, target in redirects.items():
            url = urljoin(base_url + '/', path)
            
            success, status_code, actual_location, error_msg = verify_redirect(
                session, url, target)
                
            assert success, f"Failed redirect for {url}: {error_msg}"
    
    def test_file_redirects(self, session, base_url, verify_redirect):
        """Test redirects for specific files."""
        redirects = {
            'U2F/Images/YK5.png': f"{base_url}/FIDO/Images/YK5.png",
            'U2F/yubico-u2f-ca-1.pem': f"{base_url}/PKI/yubico-fido-ca-1.pem",
            'page.adoc': f"{base_url}/page.html",
        }
        
        for path, target in redirects.items():
            url = urljoin(base_url + '/', path)
            
            success, status_code, actual_location, error_msg = verify_redirect(
                session, url, target)
                
            assert success, f"Failed redirect for {url}: {error_msg}"