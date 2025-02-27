from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# Initialize your Flask app and database
app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///petmate.db'
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Import your models here - this should be done after db is defined
from petmate import User, Pet, Playdate, playdate_pets

# No need for the if __name__ == '__main__': block when using Flask CLI