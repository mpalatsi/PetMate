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
        
        # Handle image upload - try cropped image first, then direct file upload
        image_filename = None
        cropped_image_data = request.form.get('cropped_image')
        
        if cropped_image_data and cropped_image_data.startswith('data:image'):
            # Handle cropped image data
            image_filename = save_base64_image(
                cropped_image_data, 
                'static/pet_images', 
                f"{name}_cropped",
                force_extension='jpg'
            )
        elif 'pet_image' in request.files and request.files['pet_image'].filename:
            # Handle direct file upload
            file = request.files['pet_image']
            if file and allowed_file(file.filename, {'jpg', 'jpeg', 'png', 'gif'}):
                image_filename = save_uploaded_file(
                    file, 
                    'static/pet_images', 
                    f"{name}_direct",
                    force_extension='jpg'
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
        
        db.session.add(new_pet)
        db.session.commit()
        
        flash('Pet added successfully!', 'success')
        return redirect(url_for('pets.my_pets'))
    
    return render_template('add_pet.html')

@bp.route('/edit/<int:pet_id>', methods=['GET', 'POST'])
def edit_pet(pet_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))

    user = User.query.filter_by(username=session['username']).first()
    pet = Pet.query.get_or_404(pet_id)

    # Check if pet belongs to current user
    if pet.owner_id != user.id:
        flash('You can only edit your own pets.', 'error')
        return redirect(url_for('pets.my_pets'))

    if request.method == 'POST':
        old_name = pet.name
        new_name = request.form['name']
        
        # Update pet details
        pet.name = new_name
        pet.species = request.form['species']
        pet.breed = request.form['breed']
        pet.age = request.form['age']
        pet.size = request.form['size']
        pet.temperament = request.form['temperament']
        
        # Handle image upload if provided
        if 'pet_image' in request.files and request.files['pet_image'].filename:
            image = request.files['pet_image']
            if image and allowed_file(image.filename):
                # Delete old image if it exists
                if pet.image_filename:
                    old_image_path = os.path.join('static/pet_images', pet.image_filename)
                    try:
                        os.remove(old_image_path)
                    except OSError:
                        pass  # Ignore if file doesn't exist
                
                # Save new image
                image_filename = save_uploaded_file(
                    image, 
                    'static/pet_images', 
                    f"{pet.id}_{new_name}",
                    force_extension='jpg'
                )
                pet.image_filename = image_filename
        # If name changed and there's an existing image, rename it
        elif old_name != new_name and pet.image_filename:
            old_image_path = os.path.join('static/pet_images', pet.image_filename)
            new_image_filename = f"{pet.id}_{new_name}.jpg"
            new_image_path = os.path.join('static/pet_images', new_image_filename)
            try:
                os.rename(old_image_path, new_image_path)
                pet.image_filename = new_image_filename
            except OSError:
                pass  # Ignore if file doesn't exist or can't be renamed
        
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
                    image_path = os.path.join('static/pet_images', pet.image_filename)
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