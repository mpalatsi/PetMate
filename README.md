# 🐾 PetMate

## Connect, Play, Socialize: The Ultimate Pet Playdate Platform

![PetMate Banner](static/playing_dogs.jpg)

## 📋 Overview

PetMate is a web application designed to help pet owners connect with other pet parents in their local area to arrange playdates for their furry friends. The platform makes it easy to schedule meetups at parks, beaches, or other pet-friendly venues, helping pets socialize and exercise while allowing owners to build community.

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

4. Initialize the database:
   ```
   flask db init
   flask db migrate
   flask db upgrade
   ```

5. Run the application:
   ```
   flask run
   ```

6. Open your browser and navigate to `http://localhost:5000`

## 🛠️ Technology Stack

- **Backend**: Flask (Python)
- **Database**: SQLAlchemy with SQLite (development) / PostgreSQL (production)
- **Frontend**: HTML, CSS, JavaScript
- **Authentication**: Flask-Login
- **Image Processing**: Pillow, Cropper.js
- **Deployment**: Gunicorn, Nginx

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
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add some amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 📬 Contact

Project Link: [https://github.com/yourusername/petmate](https://github.com/yourusername/petmate)

---

<p align="center">Made with ❤️ for pets and their humans</p> 