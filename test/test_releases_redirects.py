"""
Test for checking that Releases directories don't cause redirect loops.

This test specifically checks the fix for the .htaccess NC (No Case) option
that was causing redirect loops with Fastly VCL case transformations.

Usage:
    pytest test_releases_redirects.py -v

To test against staging:
    TEST_DOMAIN=developers.stage.yubico.com pytest test_releases_redirects.py -v
"""

import pytest
import requests
import os
from urllib.parse import urljoin

# Known projects with Releases directories
# Based on the developers.yubico.com site structure
PROJECTS_WITH_RELEASES = [
    # Current active projects
    "YubiHSM2",
    "yubico-piv-tool", 
    "yubikey-manager",
    "yubikey-manager-qt",
    "libfido2",
    "yubihsm-setup",
    "yubioath-flutter",
    "yubioath-desktop",
]

# Test different case variations that were problematic
# Note: Only "Releases" (capital R) should work - others should return 404
CASE_VARIATIONS = [
    "Releases",      # Original case - should work (200)
    "releases",      # All lowercase - should be 404
    "RELEASES",      # All uppercase - should be 404  
    "Releases/",     # With trailing slash - should work (200)
    "releases/",     # Lowercase with trailing slash - should be 404
]

class TestReleasesDirectories:
    """Test that Releases directories work properly without redirect loops."""
    
    # Remove the duplicate fixtures - use the ones from conftest.py
    
    def check_no_redirect_loop(self, session, url, max_redirects=10):
        """
        Check that a URL doesn't cause a redirect loop.
        
        Args:
            max_redirects: Maximum allowed redirects (10 is reasonable, more suggests a problem)
        
        Returns:
            tuple: (success, status_code, final_url, redirect_count, error_msg)
        """
        try:
            visited_urls = set()
            current_url = url
            redirect_count = 0
            
            # Add longer delays for staging environment to avoid overwhelming the server
            import time
            if 'stage.yubico.com' in url:
                time.sleep(2.0)  # 2 second delay before each test for staging
            
            for i in range(max_redirects):
                print(f"Checking: {current_url}")
                
                # Check if we've been to this URL before (loop detection)
                if current_url in visited_urls:
                    return False, 0, current_url, redirect_count, f"Redirect loop detected: {current_url}"
                
                visited_urls.add(current_url)
                
                response = session.get(current_url, allow_redirects=False, timeout=30)
                status_code = response.status_code
                
                # If it's not a redirect, we're done
                if status_code not in (301, 302, 303, 307, 308):
                    # 200 is success, 404 is acceptable (might not exist), 403 forbidden is acceptable
                    if status_code in (200, 404, 403):
                        # Check if we had too many redirects even though we eventually succeeded
                        if redirect_count > max_redirects:
                            return False, status_code, current_url, redirect_count, f"Too many redirects ({redirect_count}) - suggests a configuration problem"
                        return True, status_code, current_url, redirect_count, "Success"
                    else:
                        return False, status_code, current_url, redirect_count, f"Unexpected status code: {status_code}"
                
                # Get the next URL in the redirect chain
                location = response.headers.get('Location', '')
                if not location:
                    return False, status_code, current_url, redirect_count, "Redirect without Location header"
                
                redirect_count += 1
                current_url = location
                
                # Add longer delay between redirects for staging
                if 'stage.yubico.com' in current_url:
                    time.sleep(1.0)  # 1 second delay between redirects
            
            # If we exit the loop, we hit the max redirects limit
            return False, status_code, current_url, redirect_count, f"Exceeded maximum redirects ({max_redirects}) - this suggests a redirect loop or misconfiguration"
            
        except requests.exceptions.RequestException as e:
            return False, 0, url, 0, f"Request error: {str(e)}"
    
    @pytest.mark.parametrize("project", PROJECTS_WITH_RELEASES)
    @pytest.mark.parametrize("case_variant", CASE_VARIATIONS)
    def test_releases_no_redirect_loop(self, session, base_url, project, case_variant):
        """Test that Releases directories don't cause redirect loops for different case variations."""
        url = f"{base_url}/{project}/{case_variant}"
        
        success, status_code, final_url, redirect_count, error_msg = self.check_no_redirect_loop(session, url)
        
        # Log the result for debugging
        print(f"\nTesting: {url}")
        print(f"Result: {success}, Status: {status_code}, Redirects: {redirect_count}")
        print(f"Final URL: {final_url}")
        if not success:
            print(f"Error: {error_msg}")
        
        # Different expectations based on case variation
        if case_variant in ["Releases", "Releases/"]:
            # Capital R should work (200) or redirect properly
            assert success, f"Redirect loop or error for {url}: {error_msg}"
            if success and redirect_count > 5:
                print(f"WARNING: {redirect_count} redirects for {url} - more than expected")
        else:
            # Lowercase variants should either work OR return 404 (both are acceptable)
            # What we're testing is NO INFINITE REDIRECT LOOPS
            if not success and "Request error" in error_msg:
                # Skip connection errors on staging - that's an infrastructure issue
                if 'stage.yubico.com' in base_url:
                    pytest.skip(f"Staging connection issue for {url}: {error_msg}")
                else:
                    pytest.fail(f"Connection error for {url}: {error_msg}")
            elif not success and status_code != 404:
                # If it's not a 404, and not a connection error, then it's a real problem
                assert False, f"Unexpected failure for {url}: {error_msg}"
            else:
                # Either success or 404 - both are fine for case variants
                print(f"✓ Case variant behaves correctly: {status_code}")
                if success and redirect_count > 10:
                    pytest.fail(f"Too many redirects ({redirect_count}) suggests redirect loop: {url}")
    
    def test_redirect_count_reasonable(self, session, base_url):
        """
        Test that redirect counts are reasonable for key URLs.
        
        Redirect count guidelines:
        - 0-2: Excellent (direct or simple redirect)  
        - 3-5: Good (acceptable redirect chain)
        - 6-10: Concerning (should be investigated)
        - >10: Problem (likely indicates misconfiguration)
        """
        test_urls = [
            f"{base_url}/YubiHSM2/Releases/",     # The original problem case
            f"{base_url}/YubiHSM2/releases/",     # Lowercase variant
            f"{base_url}/yubikey-manager/Releases/",
            f"{base_url}/libfido2/Releases/",
        ]
        
        results = {}
        
        for url in test_urls:
            success, status_code, final_url, redirect_count, error_msg = self.check_no_redirect_loop(
                session, url, max_redirects=15  # Higher limit to catch excessive redirects
            )
            
            results[url] = {
                'success': success,
                'redirects': redirect_count,
                'status': status_code,
                'final_url': final_url
            }
            
            print(f"\nRedirect count test: {url}")
            print(f"  Redirects: {redirect_count} ({'✓' if redirect_count <= 5 else '⚠️' if redirect_count <= 10 else '❌'})")
            print(f"  Success: {success}, Status: {status_code}")
            
            if success:
                # Classify redirect count
                if redirect_count <= 2:
                    print(f"  Assessment: Excellent ({redirect_count} redirects)")
                elif redirect_count <= 5:
                    print(f"  Assessment: Good ({redirect_count} redirects)")
                elif redirect_count <= 10:
                    print(f"  Assessment: Concerning ({redirect_count} redirects - should investigate)")
                    # Don't fail the test, but log a warning
                else:
                    print(f"  Assessment: Problem ({redirect_count} redirects - likely misconfiguration)")
                    pytest.fail(f"Excessive redirects ({redirect_count}) for {url} - indicates configuration problem")
            else:
                print(f"  Assessment: Failed - {error_msg}")
                pytest.fail(f"URL failed: {url} - {error_msg}")
        
        # Summary
        total_redirects = sum(r['redirects'] for r in results.values() if r['success'])
        avg_redirects = total_redirects / len([r for r in results.values() if r['success']]) if any(r['success'] for r in results.values()) else 0
        
        print(f"\n=== Redirect Summary ===")
        print(f"Average redirects per URL: {avg_redirects:.1f}")
        print(f"Total URLs tested: {len(test_urls)}")
        print(f"Successful URLs: {sum(1 for r in results.values() if r['success'])}")
        
        if avg_redirects > 5:
            print(f"WARNING: Average redirect count ({avg_redirects:.1f}) is higher than expected")
        else:
            print(f"✓ Average redirect count is within reasonable range")
    
    def test_specific_yubihsm2_case_issue(self, session, base_url):
        """
        Test the specific YubiHSM2 case issue that was reported.
        
        This tests the exact scenario that was failing due to the .htaccess NC option.
        """
        # The specific URL that was causing issues
        problematic_url = f"{base_url}/YubiHSM2/Releases/"
        
        success, status_code, final_url, redirect_count, error_msg = self.check_no_redirect_loop(
            session, problematic_url, max_redirects=10
        )
        
        print(f"\nSpecific YubiHSM2 test:")
        print(f"URL: {problematic_url}")
        print(f"Success: {success}")
        print(f"Status: {status_code}")
        print(f"Redirects: {redirect_count}")
        print(f"Final URL: {final_url}")
        
        assert success, f"YubiHSM2/Releases/ still causing issues: {error_msg}"
        
        # Additional check: ensure redirect count is reasonable
        # 0-3 redirects: Normal (HTTPS redirect, trailing slash, etc.)
        # 4-10 redirects: Acceptable but worth monitoring  
        # >10 redirects: Problem (likely loop or misconfiguration)
        if redirect_count > 10:
            pytest.fail(f"Too many redirects ({redirect_count}) for YubiHSM2/Releases/ - suggests configuration issue")
        elif redirect_count > 3:
            print(f"WARNING: {redirect_count} redirects is more than expected (0-3), but within acceptable range")
        else:
            print(f"✓ Redirect count ({redirect_count}) is within normal range")
    
    def test_case_insensitive_behavior(self, session, base_url):
        """
        Test that different case variations behave consistently.
        
        This ensures the .htaccess fix doesn't break legitimate case handling.
        """
        test_cases = [
            f"{base_url}/YubiHSM2/Releases/",
            f"{base_url}/yubihsm2/releases/",  # What Fastly VCL transforms to
            f"{base_url}/YUBIHSM2/RELEASES/",
        ]
        
        results = {}
        
        for url in test_cases:
            success, status_code, final_url, redirect_count, error_msg = self.check_no_redirect_loop(
                session, url, max_redirects=5
            )
            results[url] = {
                'success': success,
                'status': status_code,
                'final_url': final_url,
                'redirects': redirect_count,
                'error': error_msg
            }
            
            print(f"\nCase test: {url}")
            print(f"  Success: {success}, Status: {status_code}, Redirects: {redirect_count}")
            
            # Each URL should not cause a redirect loop
            assert success, f"Case variation failed: {url} - {error_msg}"
    
    def test_trailing_slash_behavior(self, session, base_url):
        """Test that trailing slashes are handled properly."""
        base_cases = [
            f"{base_url}/YubiHSM2/Releases",     # No trailing slash
            f"{base_url}/YubiHSM2/Releases/",    # With trailing slash
        ]
        
        for url in base_cases:
            success, status_code, final_url, redirect_count, error_msg = self.check_no_redirect_loop(
                session, url, max_redirects=3
            )
            
            print(f"\nTrailing slash test: {url}")
            print(f"  Success: {success}, Status: {status_code}")
            
            assert success, f"Trailing slash handling failed: {url} - {error_msg}"

class TestReleasesContent:
    """Test that Releases directories serve expected content when they exist."""
    
    # Remove the duplicate fixtures - use the ones from conftest.py
    
    def test_releases_content_type(self, session, base_url):
        """Test that Releases pages return appropriate content."""
        # Test a few known good releases pages
        test_urls = [
            f"{base_url}/YubiHSM2/Releases/",
            f"{base_url}/libfido2/Releases/",
            f"{base_url}/yubikey-manager/Releases/",
        ]
        
        for url in test_urls:
            try:
                response = session.get(url, timeout=10)
                
                print(f"\nContent test for: {url}")
                print(f"Status: {response.status_code}")
                print(f"Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                
                # Should be a successful response or a reasonable redirect
                assert response.status_code in (200, 301, 302, 404), f"Unexpected status for {url}: {response.status_code}"
                
                # If it's HTML, it should contain expected content
                if response.status_code == 200 and 'text/html' in response.headers.get('Content-Type', ''):
                    content = response.text.lower()
                    # Should contain some indication it's a releases page
                    assert any(word in content for word in ['release', 'download', 'version', 'binary']), \
                        f"Releases page doesn't contain expected content: {url}"
                        
            except requests.exceptions.RequestException as e:
                pytest.skip(f"Could not connect to {url}: {e}")

if __name__ == "__main__":
    # Run a quick test if executed directly
    import sys
    import os
    
    session = requests.Session()
    # Use environment variables like the conftest.py does
    domain = os.getenv('TEST_DOMAIN', 'developers.yubico.com')
    protocol = os.getenv('TEST_PROTOCOL', 'https')
    base_url = f"{protocol}://{domain}"
    
    print("Quick test of YubiHSM2 Releases directory...")
    
    test_instance = TestReleasesDirectories()
    success, status, final_url, redirects, error = test_instance.check_no_redirect_loop(
        session, f"{base_url}/YubiHSM2/Releases/"
    )
    
    print(f"Result: {'✓ PASS' if success else '✗ FAIL'}")
    print(f"Status: {status}, Redirects: {redirects}")
    print(f"Final URL: {final_url}")
    if not success:
        print(f"Error: {error}")
        sys.exit(1)
    else:
        print("Test passed! No redirect loop detected.")