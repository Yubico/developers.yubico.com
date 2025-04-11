"""
Tests for redirect functionality on the Yubico developers website.

This module tests that:
1. EOL projects redirect to the proper EOL policy page
2. Standard redirects work as expected

Usage:
    pytest test_redirects.py -v

To test against local development:
    TEST_DOMAIN=localhost:8080 TEST_PROTOCOL=http pytest test_redirects.py -v
"""

import pytest
import os
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
    
    def test_case_sensitivity_redirects(self, session, base_url, verify_redirect):
        """Test case-sensitivity redirects (lowercase to proper case)."""
        redirects = {
            'yubihsm2': f"{base_url}/YubiHSM2/",
            'u2f': f"{base_url}/U2F/",
            'ssh': f"{base_url}/SSH/",
            'mobile': f"{base_url}/Mobile/",
            'mobile_dev': f"{base_url}/Mobile_Dev/",
            'passkeys': f"{base_url}/Passkeys/",
            'developer-program': f"{base_url}/Developer_Program/",
            'fido2': f"{base_url}/WebAuthn/",
        }
        
        for path, target in redirects.items():
            url = urljoin(base_url + '/', path)
            
            success, status_code, actual_location, error_msg = verify_redirect(
                session, url, target)
                
            assert success, f"Failed redirect for {url}: {error_msg}"
    
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
    
    def test_path_structure_redirects(self, session, base_url, verify_redirect):
        """Test redirects for path structure changes."""
        redirects = {
            'some-project/releases/v1.0': f"{base_url}/some-project/Releases/v1.0",
            'some-project/releases.html': f"{base_url}/some-project/Releases/",
            'some-project/doc/manual': f"{base_url}/some-project/manual",
        }
        
        for path, target in redirects.items():
            url = urljoin(base_url + '/', path)
            
            success, status_code, actual_location, error_msg = verify_redirect(
                session, url, target)
                
            assert success, f"Failed redirect for {url}: {error_msg}"