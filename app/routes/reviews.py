from flask import Blueprint, render_template, redirect, url_for, session, request, flash
from app.models.user import User
from app.models.review import Review
from app.models.playdate import Playdate
from app import db
from datetime import datetime

bp = Blueprint('reviews', __name__, url_prefix='/reviews')

@bp.route('/create/<int:playdate_id>', methods=['GET', 'POST'])
def create_review(playdate_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if user was part of the playdate
    is_participant = False
    for pet in playdate.pets:
        if pet.owner_id == user.id:
            is_participant = True
            break
    
    if playdate.host_id != user.id and not is_participant:
        flash('You cannot review a playdate you were not part of.', 'error')
        return redirect(url_for('playdates.playdates'))
    
    # Check if user has already reviewed this playdate
    existing_review = Review.query.filter_by(
        reviewer_id=user.id,
        playdate_id=playdate_id
    ).first()
    
    if existing_review:
        flash('You have already reviewed this playdate.', 'info')
        return redirect(url_for('reviews.view_reviews', playdate_id=playdate_id))
    
    if request.method == 'POST':
        rating = request.form.get('rating')
        comments = request.form.get('comments')
        
        # Determine who is being reviewed
        # If the current user is the host, they are reviewing a participant
        # If the current user is a participant, they are reviewing the host
        if playdate.host_id == user.id:
            # Host is reviewing a participant
            # In this case, we need to know which participant they're reviewing
            reviewed_user_id = request.form.get('reviewed_user_id')
            if not reviewed_user_id:
                flash('Please select a user to review.', 'error')
                return render_template(
                    'create_review.html', 
                    playdate=playdate,
                    is_host=True
                )
        else:
            # Participant is reviewing the host
            reviewed_user_id = playdate.host_id
        
        # Create the review
        new_review = Review(
            reviewer_id=user.id,
            reviewed_id=reviewed_user_id,
            playdate_id=playdate_id,
            rating=rating,
            comments=comments,
            created_at=datetime.now()
        )
        
        try:
            db.session.add(new_review)
            db.session.commit()
            flash('Review submitted successfully!', 'success')
            return redirect(url_for('reviews.view_reviews', playdate_id=playdate_id))
        except Exception as e:
            db.session.rollback()
            flash(f'Error submitting review: {str(e)}', 'error')
    
    # Determine if the current user is the host
    is_host = (playdate.host_id == user.id)
    
    # If the user is the host, get list of participants to review
    participants = []
    if is_host:
        # Get unique owners of pets in the playdate
        participant_ids = set()
        for pet in playdate.pets:
            if pet.owner_id != user.id:  # Exclude the host's pets
                participant_ids.add(pet.owner_id)
        
        # Get user objects for all participants
        for participant_id in participant_ids:
            participant = User.query.get(participant_id)
            if participant:
                participants.append(participant)
    
    return render_template(
        'create_review.html', 
        playdate=playdate,
        is_host=is_host,
        participants=participants
    )

@bp.route('/view/<int:playdate_id>')
def view_reviews(playdate_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if user was part of the playdate
    is_participant = False
    for pet in playdate.pets:
        if pet.owner_id == user.id:
            is_participant = True
            break
    
    if playdate.host_id != user.id and not is_participant:
        flash('You cannot view reviews for a playdate you were not part of.', 'error')
        return redirect(url_for('playdates.playdates'))
    
    # Get all reviews for this playdate
    reviews = Review.query.filter_by(playdate_id=playdate_id).all()
    
    # Check if the current user has already submitted a review
    user_has_reviewed = any(review.reviewer_id == user.id for review in reviews)
    
    return render_template(
        'view_reviews.html',
        playdate=playdate,
        reviews=reviews,
        user_has_reviewed=user_has_reviewed,
        current_user=user
    )

@bp.route('/user/<int:user_id>')
def user_reviews(user_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    reviewed_user = User.query.get_or_404(user_id)
    
    # Get all reviews where this user was reviewed
    reviews = Review.query.filter_by(reviewed_id=user_id).all()
    
    # Calculate average rating
    total_ratings = sum(review.rating for review in reviews if review.rating)
    avg_rating = total_ratings / len(reviews) if reviews else 0
    
    return render_template(
        'user_reviews.html',
        user=reviewed_user,
        reviews=reviews,
        avg_rating=avg_rating
    ) 