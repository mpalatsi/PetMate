import pytest
import time
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By

# Import the Page Object Models using relative imports
from .page_objects.login_page import LoginPage
from .page_objects.dashboard_page import DashboardPage

# Mark all tests in this class as nondestructive
@pytest.mark.nondestructive
class TestLogin:
    """Test suite for login functionality"""
    
    def test_successful_login(self, chrome_driver, base_url):
        """Test successful login with valid credentials"""
        try:
            # Initialize page objects
            login_page = LoginPage(chrome_driver, base_url)
            dashboard_page = DashboardPage(chrome_driver, base_url)
            
            # Navigate to login page
            login_page.navigate()
            
            # Verify we're on the login page (more flexible assertion)
            assert "Login" in chrome_driver.title or "PetMate" in chrome_driver.title, "Not on login page"
            
            # Perform login
            login_page.login("selenium_test", "test123")
            
            # Wait for redirect
            try:
                login_page.wait_for_redirect()
            except:
                pytest.fail("Login did not redirect from login page")
            
            # Check if we landed on index page or dashboard
            assert dashboard_page.is_on_index_page() or dashboard_page.check_url_contains_dashboard(), \
                f"Not redirected to index or dashboard. Current URL: {chrome_driver.current_url}"
                
            # Take a screenshot for verification
            chrome_driver.save_screenshot("successful_login.png")
        except Exception as e:
            chrome_driver.save_screenshot("error_successful_login.png")
            raise e
    
    def test_failed_login_invalid_credentials(self, chrome_driver, base_url):
        """Test login failure with invalid credentials"""
        try:
            # Initialize page object
            login_page = LoginPage(chrome_driver, base_url)
            
            # Navigate to login page
            login_page.navigate()
            
            # Perform login with invalid credentials
            login_page.login("wrong_user", "wrong_password")
            
            # Check for error message
            time.sleep(1)  # Small wait to ensure error is displayed
            assert login_page.is_error_displayed(), "Error message not displayed after failed login"
            
            # Take a screenshot for verification
            chrome_driver.save_screenshot("failed_login.png")
            
            # Verify we're still on login page
            assert "/auth/login" in chrome_driver.current_url, "Redirected away from login page after failed login"
        except Exception as e:
            chrome_driver.save_screenshot("error_failed_login.png")
            raise e
    
    def test_admin_login(self, chrome_driver, base_url):
        """Test successful login with admin credentials"""
        try:
            # Initialize page objects
            login_page = LoginPage(chrome_driver, base_url)
            dashboard_page = DashboardPage(chrome_driver, base_url)
            
            # Navigate to login page
            login_page.navigate()
            
            # Perform login with admin credentials
            login_page.login("selenium_admin", "admin123")
            
            # Wait for redirect
            try:
                login_page.wait_for_redirect()
            except:
                pytest.fail("Admin login did not redirect from login page")
            
            # Check for admin dashboard access
            WebDriverWait(chrome_driver, 10).until(
                lambda driver: "/admin" in driver.current_url or dashboard_page.is_on_index_page()
            )
            
            # Take a screenshot for verification
            chrome_driver.save_screenshot("admin_login.png")
        except Exception as e:
            chrome_driver.save_screenshot("error_admin_login.png")
            raise e
    
    def test_login_logout_flow(self, chrome_driver, base_url):
        """Test full login and logout flow"""
        try:
            # Initialize page objects
            login_page = LoginPage(chrome_driver, base_url)
            dashboard_page = DashboardPage(chrome_driver, base_url)
            
            # Navigate to login page
            login_page.navigate()
            
            # Perform login
            login_page.login("selenium_test", "test123")
            
            # Wait for redirect
            login_page.wait_for_redirect()
            
            # Verify login was successful
            assert dashboard_page.is_on_index_page() or dashboard_page.check_url_contains_dashboard(), \
                "Not redirected to index or dashboard after login"
            
            # Perform logout
            assert dashboard_page.logout(), "Logout link not found or not clickable"
            
            # Verify we're back at login or index page
            WebDriverWait(chrome_driver, 10).until(
                lambda driver: "/login" in driver.current_url or driver.current_url == f"{base_url}/"
            )
            
            # Take a screenshot for verification
            chrome_driver.save_screenshot("logout_result.png")
        except Exception as e:
            chrome_driver.save_screenshot("error_logout_flow.png")
            raise e 