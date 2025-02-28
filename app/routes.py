from datetime import datetime
from app import app, db
from app.models import User, Pet, Playdate, PlaydateMessage
from flask import render_template, redirect, url_for, flash, request, session
from sqlalchemy.exc import IntegrityError
import os
import time
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.route('/playdates/<int:playdate_id>/chat')
def playdate_group_chat(playdate_id):
    if 'user_id' not in session:
        flash('Please log in to view this page.', 'error')
        return redirect(url_for('login'))
    
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if the current user is a participant
    user_id = session['user_id']
    if user_id != playdate.host_id and user_id not in [participant.id for participant in playdate.participants]:
        flash('You are not a participant in this playdate.', 'error')
        return redirect(url_for('dashboard'))
    
    # Get the current user
    user = User.query.get(user_id)
    
    # Get all participants including host
    host = User.query.get(playdate.host_id)
    participants = [host] + [p for p in playdate.participants if p.id != playdate.host_id]
    
    # Store username in session for WebSocket use
    session['username'] = user.username
    
    return render_template('playdate_group_chat.html', 
                          playdate=playdate, 
                          participants=participants, 
                          host=host,
                          current_user=user) 