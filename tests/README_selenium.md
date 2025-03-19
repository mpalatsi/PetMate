# Selenium Testing for PetMate

This document provides instructions for setting up and running Selenium tests for the PetMate application.

## Prerequisites

- Python 3.7 or higher
- Chrome browser installed
- PetMate application running locally

## Installation

1. Install the required packages:

```bash
pip install -r test_requirements.txt
```

2. Make sure the Chrome browser is installed on your system.

## Running Tests

1. Start the Flask server in a separate terminal:

```bash
python app.py
```

2. Run the Selenium tests:

```bash
python -m pytest tests/test_selenium_login.py -v
```

To run a specific test:

```bash
python -m pytest tests/test_selenium_login.py::TestLogin::test_successful_login -v
```

## Test Structure

The Selenium tests are organized using the Page Object Model pattern:

- `tests/selenium_conftest.py` - Test fixtures for Selenium tests
- `tests/page_objects/` - Page object classes
  - `login_page.py` - Page object for the login page
  - `dashboard_page.py` - Page object for the dashboard page
- `tests/test_selenium_login.py` - Test cases for login functionality

## Screenshots

Screenshots are automatically saved in the project root directory after each test:

- `successful_login.png` - Screenshot after successful login
- `failed_login.png` - Screenshot after failed login
- `admin_login.png` - Screenshot after admin login
- `logout_result.png` - Screenshot after logout

## Adding New Tests

To add new Selenium tests:

1. Create new page objects in the `tests/page_objects/` directory
2. Create test files with a `test_selenium_` prefix
3. Add test methods within test classes

## Troubleshooting

- If tests fail due to timing issues, try increasing the timeout values in the wait methods
- If elements are not found, check the selectors in the page objects
- Chrome WebDriver is managed automatically, but you may need to update Chrome 