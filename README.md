# 🐾 PetMate

## Connect, Play, Socialize: The Ultimate Pet Playdate Platform

![PetMate Banner](static/playing_dogs.jpg)

## 📋 Overview

PetMate is a web application that helps pet owners find playmates for their pets. It allows users to create profiles for their pets, search for compatible playmates, schedule playdates, and communicate with other pet owners.

## ✨ Features

### For Pet Parents
- **Create Pet Profiles**: Add your pets with photos, breed information, temperament, and other details
- **Find Local Playdates**: Search for compatible playmates in your neighborhood
- **Schedule Meetups**: Organize playdates at convenient times and locations
- **RSVP System**: Confirm, tentatively accept, or decline playdate invitations
- **User Profiles**: Customize your profile with a photo and bio

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
   ```
   git clone https://github.com/yourusername/petmate.git
   cd petmate
   ```

2. Create and activate a virtual environment:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Set up environment variables:
   ```
   export FLASK_APP=petmate.py
   export FLASK_ENV=development
   ```
   On Windows:
   ```
   set FLASK_APP=petmate.py
   set FLASK_ENV=development
   ```

5. Initialize the database:
   ```
   flask create-tables
   ```

6. (Optional) Seed the database with sample data:
   ```
   flask seed-data
   ```

7. Run the application:
   ```
   flask run
   ```
   or
   ```
   python petmate.py
   ```

8. Access the application at http://localhost:5000

## 🛠️ Technology Stack

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

---

<p align="center">Made with ❤️ for pets and their humans</p> 