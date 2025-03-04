import sys
import os
import requests
import random
from PIL import Image
from io import BytesIO

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from app import db, create_app
from app.models.user import User
from app.models.pet import Pet
from datetime import datetime
from werkzeug.security import generate_password_hash

def download_and_save_image(url, save_path):
    try:
        response = requests.get(url)
        if response.status_code == 200:
            img = Image.open(BytesIO(response.content))
            img.save(save_path)
            return os.path.basename(save_path)
    except Exception as e:
        print(f"Error downloading image from {url}: {str(e)}")
    return None

def get_random_user_image():
    # Using thispersondoesnotexist.com API for random human faces
    image_url = "https://thispersondoesnotexist.com/"
    save_path = f"app/static/test_images/users/user_{random.randint(1000, 9999)}.jpg"
    return download_and_save_image(image_url, save_path)

def get_random_pet_image(species, pet_id):
    # Using placedog.net for all pet images
    width = random.randint(400, 600)
    height = random.randint(400, 600)
    image_url = f"https://placedog.net/{width}/{height}"
    
    save_path = f"app/static/test_images/pets/pet_{pet_id}.jpg"
    return download_and_save_image(image_url, save_path)

def create_test_data():
    app = create_app()
    with app.app_context():
        # Delete existing users and pets (cascade will handle pet deletion)
        User.query.delete()
        db.session.commit()
        
        # Create test users with their pets
        test_users = [
            {
                'username': 'sarah_dog_lover',
                'email': 'sarah@example.com',
                'name': 'Sarah Johnson',
                'password': 'Sarah123!',  # Will be removed before creating User
                'bio': 'Dog enthusiast and professional trainer with 5 years of experience.',
                'location': 'Boston, MA',
                'preferred_meetup_types': 'parks,dog runs,beaches',
                'availability': 'weekends,evenings',
                'pet_owner_since': 2018,
                'pet_experience_level': 'expert',
                'pets': [
                    {
                        'name': 'Max',
                        'species': 'Dog',
                        'breed': 'Golden Retriever',
                        'age': 3,
                        'size': 'Large',
                        'gender': 'Male',
                        'energy_level': 'High',
                        'friendliness': 'Outgoing',
                        'training_level': 'Advanced',
                        'bio': 'Friendly and energetic Golden who loves to play fetch!'
                    }
                ]
            },
            {
                'username': 'mike_pet_dad',
                'email': 'mike@example.com',
                'name': 'Michael Chen',
                'password': 'Mike123!',  # Will be removed before creating User
                'bio': 'Proud pet parent to both cats and dogs. Love organizing pet meetups!',
                'location': 'Cambridge, MA',
                'preferred_meetup_types': 'indoor play areas,parks',
                'availability': 'weekdays,mornings',
                'pet_owner_since': 2019,
                'pet_experience_level': 'intermediate',
                'pets': [
                    {
                        'name': 'Luna',
                        'species': 'Cat',
                        'breed': 'Siamese',
                        'age': 2,
                        'size': 'Medium',
                        'gender': 'Female',
                        'energy_level': 'Medium',
                        'friendliness': 'Moderate',
                        'training_level': 'Basic',
                        'bio': 'Elegant Siamese who enjoys supervised outdoor adventures.'
                    },
                    {
                        'name': 'Rocky',
                        'species': 'Dog',
                        'breed': 'French Bulldog',
                        'age': 1,
                        'size': 'Small',
                        'gender': 'Male',
                        'energy_level': 'High',
                        'friendliness': 'Outgoing',
                        'training_level': 'Intermediate',
                        'bio': 'Playful Frenchie who loves meeting new friends!'
                    }
                ]
            },
            {
                'username': 'emma_paws',
                'email': 'emma@example.com',
                'name': 'Emma Wilson',
                'password': 'Emma123!',  # Will be removed before creating User
                'bio': 'Animal shelter volunteer and pet photography enthusiast.',
                'location': 'Somerville, MA',
                'preferred_meetup_types': 'parks,pet cafes',
                'availability': 'weekends,afternoons',
                'pet_owner_since': 2020,
                'pet_experience_level': 'intermediate',
                'pets': [
                    {
                        'name': 'Bella',
                        'species': 'Dog',
                        'breed': 'Poodle Mix',
                        'age': 2,
                        'size': 'Medium',
                        'gender': 'Female',
                        'energy_level': 'Medium',
                        'friendliness': 'Shy',
                        'training_level': 'Intermediate',
                        'bio': 'Sweet rescue poodle mix who loves gentle play sessions.'
                    }
                ]
            },
            {
                'username': 'alex_petpal',
                'email': 'alex@example.com',
                'name': 'Alex Rodriguez',
                'password': 'Alex123!',  # Will be removed before creating User
                'bio': 'Former vet tech with a passion for pet health and socialization.',
                'location': 'Brookline, MA',
                'preferred_meetup_types': 'dog parks,agility courses',
                'availability': 'flexible',
                'pet_owner_since': 2017,
                'pet_experience_level': 'expert',
                'pets': [
                    {
                        'name': 'Shadow',
                        'species': 'Dog',
                        'breed': 'Border Collie',
                        'age': 4,
                        'size': 'Medium',
                        'gender': 'Male',
                        'energy_level': 'High',
                        'friendliness': 'Moderate',
                        'training_level': 'Advanced',
                        'bio': 'Intelligent Border Collie who excels at agility training.'
                    }
                ]
            },
            {
                'username': 'lily_catmom',
                'email': 'lily@example.com',
                'name': 'Lily Thompson',
                'password': 'Lily123!',  # Will be removed before creating User
                'bio': 'Cat behavior specialist and indoor/outdoor play expert.',
                'location': 'Medford, MA',
                'preferred_meetup_types': 'indoor playdates,cat cafes',
                'availability': 'evenings,weekends',
                'pet_owner_since': 2016,
                'pet_experience_level': 'expert',
                'pets': [
                    {
                        'name': 'Oliver',
                        'species': 'Cat',
                        'breed': 'Maine Coon',
                        'age': 3,
                        'size': 'Large',
                        'gender': 'Male',
                        'energy_level': 'Medium',
                        'friendliness': 'Outgoing',
                        'training_level': 'Advanced',
                        'bio': 'Gentle giant Maine Coon who loves other cats.'
                    },
                    {
                        'name': 'Milo',
                        'species': 'Cat',
                        'breed': 'American Shorthair',
                        'age': 1,
                        'size': 'Medium',
                        'gender': 'Male',
                        'energy_level': 'High',
                        'friendliness': 'Outgoing',
                        'training_level': 'Basic',
                        'bio': 'Energetic young cat who loves to play with toys.'
                    }
                ]
            }
        ]

        # Create users and their pets with images
        for user_data in test_users:
            pets = user_data.pop('pets')
            password = user_data.pop('password')
            
            # Get a random profile picture for the user
            profile_picture = get_random_user_image()
            user = User(**user_data, profile_picture=profile_picture)
            user.set_password(password)
            db.session.add(user)
            db.session.flush()  # To get the user ID

            # Create pets with images
            for pet_data in pets:
                # Get a random pet image
                pet_image = get_random_pet_image(pet_data['species'], random.randint(1000, 9999))
                pet = Pet(**pet_data, owner_id=user.id, profile_picture=pet_image)
                db.session.add(pet)

        db.session.commit()
        print("Test data created successfully!")

if __name__ == '__main__':
    create_test_data() 