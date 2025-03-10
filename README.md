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

## ��️ Technology Stack

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