from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class LoginPage:
    """
    Page Object for the login page.
    Encapsulates the login functionality for reuse in tests.
    """
    
    # Element locators
    USERNAME_INPUT = (By.ID, "username")
    PASSWORD_INPUT = (By.ID, "password")
    LOGIN_BUTTON = (By.CSS_SELECTOR, "button[type='submit']")
    ERROR_MESSAGE = (By.CSS_SELECTOR, ".error")
    
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
    
    def navigate(self):
        """Navigate to the login page"""
        self.driver.get(f"{self.base_url}/auth/login")
        return self
    
    def enter_username(self, username):
        """Enter username in the login form"""
        username_field = self.driver.find_element(*self.USERNAME_INPUT)
        username_field.clear()
        username_field.send_keys(username)
        return self
    
    def enter_password(self, password):
        """Enter password in the login form"""
        password_field = self.driver.find_element(*self.PASSWORD_INPUT)
        password_field.clear()
        password_field.send_keys(password)
        return self
    
    def click_login(self):
        """Click the login button"""
        self.driver.find_element(*self.LOGIN_BUTTON).click()
    
    def login(self, username, password):
        """Complete the login process with the given credentials"""
        self.enter_username(username)
        self.enter_password(password)
        self.click_login()
    
    def is_error_displayed(self):
        """Check if error message is displayed"""
        try:
            return self.driver.find_element(*self.ERROR_MESSAGE).is_displayed()
        except:
            return False
    
    def get_error_message(self):
        """Get the error message text"""
        try:
            return self.driver.find_element(*self.ERROR_MESSAGE).text
        except:
            return ""
    
    def wait_for_redirect(self, timeout=10):
        """Wait for redirect after login"""
        WebDriverWait(self.driver, timeout).until(
            lambda driver: driver.current_url != f"{self.base_url}/auth/login"
        ) 