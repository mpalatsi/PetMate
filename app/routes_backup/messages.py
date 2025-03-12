from flask import Blueprint, render_template, redirect, url_for, session, request, flash, jsonify
from app.models.user import User
from app.models.message import Message
from app import db
from sqlalchemy import or_, and_
from datetime import datetime
from app.models.playdate import Playdate

bp = Blueprint('messages', __name__, url_prefix='/messages')

@bp.route('/')
def inbox():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.filter_by(username=session['username']).first()
    
    # Get conversations (grouped by the other user)
    # This query gets all messages where the current user is either sender or recipient
    messages = Message.query.filter(
        or_(
            Message.sender_id == user.id,
            Message.recipient_id == user.id
        )
    ).order_by(Message.timestamp.desc()).all()
    
    # Group messages by conversation (the other user)
    conversations = {}
    for message in messages:
        # Determine the other user in the conversation
        other_user_id = message.sender_id if message.recipient_id == user.id else message.recipient_id
        if other_user_id not in conversations:
            other_user = User.query.get(other_user_id)
            conversations[other_user_id] = {
                'user': other_user,
                'latest_message': message,
                'unread_count': 0
            }
        
        # Count unread messages
        if message.recipient_id == user.id and not message.is_read:
            conversations[other_user_id]['unread_count'] += 1
    
    # Convert dictionary to list and sort by latest message
    conversations_list = sorted(
        conversations.values(),
        key=lambda x: x['latest_message'].timestamp,
        reverse=True
    )
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    # Check if mode is explicitly specified via query parameter
    mode = request.args.get('mode', None)
    use_mobile = is_mobile and mode != 'desktop'
    
    template = 'mobile_messages.html' if use_mobile else 'messages.html'
    
    # Get total unread messages for the badge in the menu
    total_unread = sum(conv['unread_count'] for conv in conversations.values())
    
    return render_template(
        template,
        conversations=conversations_list,
        current_user=user,
        unread_messages=total_unread
    )

@bp.route('/conversation/<int:user_id>', methods=['GET', 'POST'])
def conversation(user_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    other_user = User.query.get_or_404(user_id)
    
    if request.method == 'POST':
        content = request.form.get('message')
        if content:
            new_message = Message(
                sender_id=current_user.id,
                recipient_id=user_id,
                content=content,
                timestamp=datetime.now(),
                is_read=False
            )
            db.session.add(new_message)
            db.session.commit()
    
    # Get all messages between the two users
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == user_id),
            and_(Message.sender_id == user_id, Message.recipient_id == current_user.id)
        )
    ).order_by(Message.timestamp).all()
    
    # Mark messages as read
    for message in messages:
        if message.recipient_id == current_user.id and not message.is_read:
            message.is_read = True
    
    db.session.commit()
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    # Check if mode is explicitly specified via query parameter
    mode = request.args.get('mode', None)
    use_mobile = is_mobile and mode != 'desktop'
    
    template = 'mobile_conversation.html' if use_mobile else 'conversation.html'
    
    # Get count of all unread messages for the badge in the menu
    unread_messages_count = Message.query.filter_by(
        recipient_id=current_user.id,
        is_read=False
    ).count()
    
    return render_template(
        template,
        messages=messages,
        current_user=current_user,
        other_user=other_user,
        unread_messages=unread_messages_count
    )

@bp.route('/new', methods=['GET', 'POST'])
def new_message():
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    
    if request.method == 'POST':
        recipient_username = request.form.get('recipient')
        content = request.form.get('message')
        
        recipient = User.query.filter_by(username=recipient_username).first()
        
        if not recipient:
            flash('User not found.', 'error')
            return render_template('new_message.html')
        
        if content:
            new_message = Message(
                sender_id=current_user.id,
                recipient_id=recipient.id,
                content=content,
                timestamp=datetime.now(),
                is_read=False
            )
            db.session.add(new_message)
            db.session.commit()
            
            return redirect(url_for('messages.conversation', user_id=recipient.id))
    
    # Get all users except current user
    users = User.query.filter(User.id != current_user.id).all()
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    # Check if mode is explicitly specified via query parameter
    mode = request.args.get('mode', None)
    use_mobile = is_mobile and mode != 'desktop'
    
    template = 'mobile_new_message.html' if use_mobile else 'new_message.html'
    
    return render_template(template, users=users, current_user=current_user)

@bp.route('/api/send', methods=['POST'])
def api_send_message():
    if 'username' not in session:
        return jsonify({'success': False, 'error': 'Not logged in'}), 401
    
    data = request.json
    current_user = User.query.filter_by(username=session['username']).first()
    
    if not data or 'recipient_id' not in data or 'content' not in data:
        return jsonify({'success': False, 'error': 'Missing required fields'}), 400
    
    recipient = User.query.get(data['recipient_id'])
    if not recipient:
        return jsonify({'success': False, 'error': 'Recipient not found'}), 404
    
    new_message = Message(
        sender_id=current_user.id,
        recipient_id=recipient.id,
        content=data['content'],
        timestamp=datetime.now(),
        is_read=False
    )
    
    try:
        db.session.add(new_message)
        db.session.commit()
        return jsonify({
            'success': True,
            'message': {
                'id': new_message.id,
                'content': new_message.content,
                'timestamp': new_message.timestamp.isoformat(),
                'sender_id': new_message.sender_id,
                'sender_name': current_user.name
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'error': str(e)}), 500

@bp.route('/playdate/<int:playdate_id>', methods=['GET', 'POST'])
def playdate_group_chat(playdate_id):
    if 'username' not in session:
        return redirect(url_for('auth.login'))
    
    current_user = User.query.filter_by(username=session['username']).first()
    playdate = Playdate.query.get_or_404(playdate_id)
    
    # Check if user is a participant or host of the playdate
    is_participant = False
    for pet in playdate.pets:
        if pet.owner_id == current_user.id:
            is_participant = True
            break
    
    if playdate.host_id != current_user.id and not is_participant:
        flash('You do not have permission to access this chat.', 'error')
        return redirect(url_for('playdates.view_playdate', playdate_id=playdate_id))
    
    # Get all users in this playdate (host + participants with pets)
    participants = set()
    participants.add(playdate.host_id)  # Add host
    
    for pet in playdate.pets:
        participants.add(pet.owner_id)  # Add pet owners
    
    # Remove current user from participants list
    if current_user.id in participants:
        participants.remove(current_user.id)
    
    # Get user objects for all participants
    participant_users = User.query.filter(User.id.in_(participants)).all()
    
    # Format for display
    formatted_participants = []
    for user in participant_users:
        formatted_participants.append({
            'user': user,
            'is_host': user.id == playdate.host_id
        })
    
    # Check if we should display the mobile version
    user_agent = request.headers.get('User-Agent', '').lower()
    is_mobile = any(device in user_agent for device in ['iphone', 'android', 'mobile', 'tablet'])
    
    # Check if mode is explicitly specified via query parameter
    mode = request.args.get('mode', None)
    use_mobile = is_mobile and mode != 'desktop'
    
    template = 'mobile_playdate_group_chat.html' if use_mobile else 'playdate_group_chat.html'
    
    return render_template(
        template,
        playdate=playdate,
        participants=formatted_participants,
        current_user=current_user
    ) 