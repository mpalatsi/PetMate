from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

class DashboardPage:
    """
    Page Object for the dashboard page.
    Used to verify successful login and perform dashboard-related actions.
    """
    
    # Element locators
    HEADER = (By.CSS_SELECTOR, "header")
    USERNAME_DISPLAY = (By.CSS_SELECTOR, ".user-info, .username")
    NAVIGATION = (By.CSS_SELECTOR, "nav")
    LOGOUT_LINK = (By.CSS_SELECTOR, "a[href*='logout']")
    
    def __init__(self, driver, base_url):
        self.driver = driver
        self.base_url = base_url
    
    def is_loaded(self, timeout=10):
        """Check if dashboard page is loaded"""
        try:
            WebDriverWait(self.driver, timeout).until(
                EC.presence_of_element_located(self.NAVIGATION)
            )
            return True
        except:
            return False
    
    def get_username_display(self):
        """Get the displayed username from the dashboard"""
        try:
            return self.driver.find_element(*self.USERNAME_DISPLAY).text
        except:
            # Try a few other common selectors if the first one doesn't work
            selectors = [".profile-name", "#user-profile", ".account-name"]
            for selector in selectors:
                try:
                    return self.driver.find_element(By.CSS_SELECTOR, selector).text
                except:
                    pass
            return ""
    
    def logout(self):
        """Log out from the dashboard"""
        try:
            self.driver.find_element(*self.LOGOUT_LINK).click()
            return True
        except:
            return False
    
    def check_url_contains_dashboard(self):
        """Check if the URL contains 'dashboard'"""
        return 'dashboard' in self.driver.current_url
    
    def is_on_index_page(self):
        """Check if we are on the index page after login"""
        return self.driver.current_url == f"{self.base_url}/" or self.driver.current_url == f"{self.base_url}/index" 