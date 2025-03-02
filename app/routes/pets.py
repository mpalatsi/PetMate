from flask import Blueprint, render_template, redirect, url_for, session, flash, request
from app.models.user import User
from app.models.pet import Pet
from app import db
from app.utils.helpers import allowed_file, save_uploaded_file, save_base64_image
import os

bp = Blueprint('pets', __name__, url_prefix='/pets')

@bp.route('/my_pets')
def my_pets():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    if user is None:
        return redirect(url_for('auth.login'))  # Redirect if user is not found
    
    pets = user.pets  # Assuming you have a relationship set up
    
    # Check if we should display the mobile version
    user_agent = request.user_agent.string
    is_mobile = any(device in user_agent for device in ['Android', 'iPhone', 'iPad', 'Mobile', 'webOS'])
    mode = request.args.get('mode', None)  # Check for manual override
    
    return render_template('mobile_my_pets.html' if is_mobile and mode != 'desktop' else 'my_pets.html', pets=pets)

@bp.route('/add', methods=['GET', 'POST'])
def add_pet():
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        name = request.form['name']
        species = request.form['species']
        breed = request.form['breed']
        age = request.form['age']
        size = request.form['size']
        temperament = request.form['temperament']
        cropped_image_data = request.form.get('cropped_image')
        
        # Handle image upload
        image_filename = None
        if cropped_image_data:
            image_filename = save_base64_image(
                cropped_image_data, 
                'app/static/pet_images', 
                f"{name}_cropped"
            )

        new_pet = Pet(
            name=name,
            species=species,
            breed=breed,
            age=age,
            size=size,
            temperament=temperament,
            owner_id=user.id,
            image_filename=image_filename
        )

        try:
            db.session.add(new_pet)
            db.session.commit()
            flash('Pet added successfully!', 'success')
            return redirect(url_for('pets.my_pets'))
        except Exception as e:
            db.session.rollback()
            return render_template('add_pet.html', error=f'Error adding pet: {str(e)}')

    return render_template('add_pet.html')

@bp.route('/edit/<int:pet_id>', methods=['GET', 'POST'])
def edit_pet(pet_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    # Get the current user
    current_user = User.query.filter_by(username=session['username']).first()
    
    # Get the pet from the database
    pet = Pet.query.filter_by(id=pet_id).first()
    
    # Check if pet exists and belongs to the current user
    if not pet or pet.owner_id != current_user.id:
        flash('Pet not found or you do not have permission to edit this pet.', 'error')
        return redirect(url_for('pets.my_pets'))
    
    if request.method == 'POST':
        # Update pet information
        pet.name = request.form.get('name')
        pet.species = request.form.get('species')
        pet.breed = request.form.get('breed')
        pet.age = request.form.get('age')
        pet.size = request.form.get('size')
        pet.temperament = request.form.get('temperament')
        
        # Handle image upload if provided
        if 'pet_image' in request.files and request.files['pet_image'].filename:
            image = request.files['pet_image']
            if image and allowed_file(image.filename):
                image_filename = save_uploaded_file(
                    image, 
                    'app/static/pet_images', 
                    f"{pet.id}_{pet.name}.jpg"
                )
                pet.image_filename = image_filename
        
        # Save changes to database
        db.session.commit()
        flash('Pet updated successfully!', 'success')
        return redirect(url_for('pets.my_pets'))
    
    # For GET request, display the edit form
    return render_template('edit_pet.html', pet=pet)

@bp.route('/delete/<int:pet_id>', methods=['POST'])
def delete_pet(pet_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['username']).first()
    pet = Pet.query.get(pet_id)
    
    if pet and pet.owner_id == user.id:
        try:
            # Delete pet's image file if it exists
            if pet.image_filename:
                try:
                    image_path = os.path.join('app/static/pet_images', pet.image_filename)
                    if os.path.exists(image_path):
                        os.remove(image_path)
                except Exception as e:
                    print(f"Error deleting pet image: {e}")
            
            db.session.delete(pet)
            db.session.commit()
            flash('Pet deleted successfully.', 'success')
            return redirect(url_for('pets.my_pets'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error deleting pet: {str(e)}', 'error')
            return redirect(url_for('pets.my_pets'))

    flash('Pet not found or you do not have permission to delete this pet.', 'error')
    return redirect(url_for('pets.my_pets'))

@bp.route('/pet/<int:pet_id>')
def view_pet(pet_id):
    """
    View a single pet's profile.
    
    Args:
        pet_id: The ID of the pet to view
        
    Returns:
        Rendered template for the pet's profile
    """
    # Check if user is logged in
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    # Get the current user and the requested pet
    current_user = User.query.filter_by(username=session['username']).first()
    pet = Pet.query.get_or_404(pet_id)
    
    # Get the pet's owner
    owner = User.query.get(pet.owner_id)
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    # Check if mode is explicitly specified via query parameter
    mode = request.args.get('mode', None)
    use_mobile = is_mobile and mode != 'desktop'
    
    # Set the template based on device type
    template = 'mobile_view_pet.html' if use_mobile else 'view_pet.html'
    
    # Check if the current user is the owner
    is_owner = current_user.id == pet.owner_id
    
    return render_template(
        template,
        pet=pet,
        owner=owner,
        is_owner=is_owner,
        user=current_user
    ) 