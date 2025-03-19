# Selenium Tests for PetMate

This directory contains Selenium-based automated tests for the PetMate application.

## Prerequisites

Make sure you have the following installed:

1. Python 3.7+
2. Chrome browser
3. PetMate dependencies

Install the required packages:

```bash
pip install selenium webdriver-manager pytest-selenium
```

## Running the Tests

There are multiple ways to run the Selenium tests:

### Method 1: Run with the Batch Script (Windows only)

For Windows users, simply run the batch script:

```
run_all_tests.bat
```

This will:
1. Start the Flask server in a new window
2. Wait for the server to start
3. Run the Selenium tests
4. Display the results

### Method 2: Run with PowerShell Script (Windows only)

For Windows users who prefer PowerShell:

```
.\run_all_tests.ps1
```

This will:
1. Check if port 5000 is already in use and free it if needed
2. Start the Flask server in a new PowerShell window
3. Wait for the server to start
4. Run the Selenium tests
5. Display the results

### Method 3: Manual Server Start

1. First, start the Flask server:
   ```
   python app.py
   ```

2. In a separate terminal, run the tests:
   ```
   python alt_test.py
   ```

## Test Files

- `alt_test.py`: Standalone test that connects to an existing Flask server
- `run_single_test.py`: Attempts to start the Flask server and run tests
- `run_tests.py`: More robust test runner that manages the Flask server
- `tests/test_selenium_login.py`: Pytest-based tests using Page Objects

## Page Objects

- `tests/page_objects/login_page.py`: Page object for the login page
- `tests/page_objects/dashboard_page.py`: Page object for the dashboard page

## Troubleshooting

### The Flask server doesn't start

Check if port 5000 is already in use:

```
netstat -ano | findstr :5000
```

If a process is using this port, you can terminate it:

```powershell
# PowerShell
$process = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess
Stop-Process -Id $process -Force
```

### ChromeDriver issues

If you encounter issues with ChromeDriver, make sure your Chrome browser is up to date. The webdriver-manager package should handle downloading the correct ChromeDriver version, but if it fails, you can download it manually from [ChromeDriver downloads](https://chromedriver.chromium.org/downloads).

### Test failures

If a test fails, check the screenshots generated during the test run:
- `home_page.png`
- `login_page.png`
- `after_login.png`
- `error_screenshot.png` (if an error occurred)

## Creating New Tests

1. Create new page objects in `tests/page_objects/`
2. Add new test methods to existing test classes or create new ones
3. Extend the standalone tests as needed

## Running Headless

To run tests without opening a browser window, uncomment the headless line in the test files:

```python
chrome_options.add_argument("--headless")
```

This is useful for CI/CD environments. 