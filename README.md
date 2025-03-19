# 🐾 PetMate

## Connect, Play, Socialize: The Ultimate Pet Playdate Platform

![PetMate Banner](static/playing_dogs.jpg)

## 📋 Overview

PetMate is a Flask-based web application for pet owners to connect, schedule playdates, and share photos of their pets.

## ✨ Features

### For Pet Parents
- **Create Pet Profiles**: Add your pets with photos, breed information, temperament, and other details
- **Find Local Playdates**: Search for compatible playmates in your neighborhood
- **Schedule Meetups**: Organize playdates at convenient times and locations
- **RSVP System**: Confirm, tentatively accept, or decline playdate invitations
- **User Profiles**: Customize your profile with a photo and bio
- **Photo Gallery**: Share photos of your pets
- **Messaging System**: Communicate with other pet owners
- **Admin Panel**: Manage site features and user data

### For Pets
- **Socialization**: Help your pets make friends and develop social skills
- **Exercise**: Regular playdates provide physical activity and mental stimulation
- **Compatibility**: Find playmates based on size, breed, and temperament

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Flask and dependencies (see requirements.txt)
- SQLite (for development)

### Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/petmate.git
   cd petmate
   ```

2. Create a virtual environment and activate it:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

5. Initialize the database:
   ```bash
   flask db init
   flask db migrate
   flask db upgrade
   ```

6. Create an admin user:
   ```bash
   flask create-admin
   ```

7. Run the application:
   ```bash
   python app.py
   ```

8. Access the application at http://localhost:5000

## 📄 Technology Stack

- **Backend**: Flask, SQLAlchemy
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login, Werkzeug security
- **File Uploads**: Werkzeug utilities
- **Forms**: Flask-WTF
- **Migrations**: Flask-Migrate

## 📱 Screenshots

| Home Page | Pet Profile | Playdate Scheduling |
|-----------|------------|---------------------|
| ![Home](docs/screenshots/home.png) | ![Profile](docs/screenshots/profile.png) | ![Schedule](docs/screenshots/schedule.png) |

## 🗺️ Roadmap

- [ ] Mobile app version
- [ ] In-app messaging between pet owners
- [ ] Pet playdate reviews and ratings
- [ ] Integration with popular calendar apps
- [ ] Breed-specific playdate groups
- [ ] Pet training event scheduling

## 🤝 Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Commit your changes: `git commit -m 'Add some feature'`
4. Push to the branch: `git push origin feature-name`
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📬 Contact

Project Link: [https://github.com/yourusername/petmate](https://github.com/yourusername/petmate)

## Testing

PetMate includes a comprehensive test suite. To run the tests:

```bash
python -m pytest
```

To run specific test files:

```bash
python -m pytest tests/test_auth.py
```

To run specific test functions:

```bash
python -m pytest tests/test_auth.py::TestAuth::test_register_and_login
```

To run tests with specific markers:

```bash
python -m pytest -m gallery
```

For more information on testing, see [tests/README.md](tests/README.md).

## Mobile Interface

PetMate includes a mobile-friendly interface that is automatically served to mobile devices. To force the mobile interface on desktop browsers, add `?mobile=1` to any URL.

---

<p align="center">Made with ❤️ for pets and their humans</p>

# PetMate Test Suite

This directory contains automated tests for the PetMate application.

## Prerequisites

Before running the tests, ensure you have the following installed:

1. Python 3.7 or higher
2. Flask (installed via `pip install flask`)
3. Selenium (installed via `pip install selenium`)
4. Chrome or Firefox browser
5. ChromeDriver or GeckoDriver (matching your browser version)

## Running the Tests

### Option 1: Using the Run Script (Recommended)

#### Windows Users:
1. Open Command Prompt or PowerShell
2. Navigate to the project directory
3. Run one of the following:
   - Batch file: `run_all_tests.bat`
   - PowerShell script: `.\run_all_tests.ps1`

#### Linux/Mac Users:
1. Open Terminal
2. Navigate to the project directory
3. Run: `python alt_test.py` (after manually starting the Flask server)

### Option 2: Manual Execution

1. Start the Flask server:
   ```
   python app.py
   ```
   The server runs on port 5001 by default.

2. In a separate terminal, run the tests:
   ```
   python alt_test.py
   ```

### Option 3: Running Specific Tests

You can run specific test classes or methods using the `run_single_test.py` script:

```
# Run all tests in a class
python run_single_test.py TestLogin

# Run a specific test method
python run_single_test.py TestMobile test_mobile_detection
```

Available test classes:
- `TestLogin`: Basic login functionality tests
- `TestMobile`: Mobile-specific UI and functionality tests

### Option 4: Testing with Valid Credentials

A standalone script is provided to test login with valid credentials:

```bash
python test_valid_login.py
```

This script:
1. Starts the Flask server if it's not already running
2. Creates a test user with username "test_selenium" if it doesn't exist
3. Opens Chrome via WebDriver
4. Attempts to log in with the test user's credentials
5. Takes a screenshot of the result (saved as login_result.png)
6. Reports whether the login was successful
7. Cleans up the WebDriver and Flask server

The script is designed to be robust and provide clear output about what's happening at each step.

## Test Classes and Methods

### TestLogin
- `test_01_visit_home_page`: Verifies the home page loads correctly
- `test_02_navigate_to_login`: Tests navigation to the login page
- `test_03_attempt_login_invalid`: Tests form submission with invalid credentials
- `test_04_attempt_login_valid`: Tests form submission with valid credentials (requires test user)

### TestMobile
- `test_mobile_detection`: Verifies the site detects mobile devices
- `test_mobile_dashboard_menu`: Tests the mobile navigation menu
- `test_mobile_gallery_tab_navigation`: Tests gallery tab navigation on mobile
- `test_mobile_photo_details`: Tests viewing photo details on mobile

## Troubleshooting

1. **Port Already in Use**: If port 5001 is already in use:
   - Kill the process using that port, or
   - Edit `app.py` to use a different port and update the test scripts accordingly

2. **Browser Driver Issues**:
   - Ensure your ChromeDriver or GeckoDriver is in your system PATH
   - Check that the driver version matches your browser version

3. **Test Failures**:
   - Check the console output for error details
   - Look for screenshots saved in the project directory (created during test execution)
   - For mobile tests, ensure your Chrome version supports mobile emulation
   
4. **Valid Credentials Test Failures**:
   - Ensure the Flask server is running
   - Check if the test user was created successfully
   - Examine database connection issues
   - Look at the screenshots generated during the test for clues

## Test Structure

- `alt_test.py`: Main test script containing all test classes
- `run_all_tests.bat`/`.ps1`: Scripts to automate starting the server and running tests
- `run_single_test.py`: Script to run specific test classes or methods
- `run_tests.py`: Alternative script for running tests with more options
- `create_test_user.py`: Script to create a test user for valid credential testing
- `run_login_test.py`: Script to run the login test with valid credentials
- `test_valid_login.py`: Standalone script for testing login with valid credentials

## Adding New Tests

To add new tests:
1. Create a new test method in an existing test class in `alt_test.py`
2. Follow the existing pattern of test methods
3. Ensure proper setup and teardown of test environment

## Reporting Issues

If you encounter any issues with the tests, please:
1. Take a screenshot of the error
2. Note the steps to reproduce
3. Open an issue in the project repository