from flask import request, session
from flask_socketio import emit, join_room, leave_room
from app import db
from app.models.user import User
from app.models.playdate import Playdate
from app.models.playdate_message import PlaydateMessage
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def register_socket_events(socketio):
    """Register SocketIO event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """Handle client connection"""
        logger.info(f"Client connected: {request.sid} - User: {session.get('username', 'Anonymous')}")
        emit('connection_response', {'status': 'connected', 'sid': request.sid})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"Client disconnected: {request.sid} - User: {session.get('username', 'Anonymous')}")
    
    @socketio.on('join_playdate_room')
    def handle_join_playdate_room(data):
        """
        Handle client joining a playdate chat room
        
        Args:
            data: Dictionary containing playdate_id
        """
        playdate_id = data.get('playdate_id')
        if not playdate_id:
            emit('error', {'message': 'Playdate ID is required'})
            return
        
        if 'user_id' not in session:
            emit('error', {'message': 'You must be logged in to join a playdate chat'})
            return
        
        user = User.query.get(session['user_id'])
        if not user:
            emit('error', {'message': 'User not found'})
            return
        
        # Join the room
        room = f"playdate_{playdate_id}"
        join_room(room)
        logger.info(f"User {user.username} (ID: {user.id}) joined room: {room}")
        
        # Notify others that user has joined
        emit('user_joined', {
            'message': f"{user.username} has joined the chat",
            'user_id': user.id,
            'username': user.username,
            'profile_picture': user.profile_picture
        }, room=room, include_self=False)
        
        # Get existing messages for this playdate
        messages = PlaydateMessage.query.filter_by(playdate_id=playdate_id).order_by(PlaydateMessage.timestamp).all()
        
        # Send history to the user
        formatted_messages = []
        for msg in messages:
            sender = User.query.get(msg.sender_id)
            formatted_messages.append({
                'id': msg.id,
                'content': msg.content,
                'sender_id': msg.sender_id,
                'sender_username': sender.username if sender else 'Unknown',
                'timestamp': msg.timestamp.isoformat(),
                'formatted_time': msg.timestamp.strftime('%I:%M %p')
            })
        
        emit('message_history', {'messages': formatted_messages}, room=request.sid)
    
    @socketio.on('leave_playdate_room')
    def handle_leave_playdate_room(data):
        """
        Handle client leaving a playdate chat room
        
        Args:
            data: Dictionary containing playdate_id
        """
        playdate_id = data.get('playdate_id')
        if not playdate_id:
            return
        
        if 'user_id' not in session:
            return
        
        user = User.query.get(session['user_id'])
        if not user:
            return
        
        room = f"playdate_{playdate_id}"
        leave_room(room)
        logger.info(f"User {user.username} (ID: {user.id}) left room: {room}")
        
        # Notify others that user has left
        emit('user_left', {
            'message': f"{user.username} has left the chat",
            'user_id': user.id,
            'username': user.username
        }, room=room)
    
    @socketio.on('playdate_message')
    def handle_playdate_message(data):
        """
        Handle new message in a playdate chat
        
        Args:
            data: Dictionary containing playdate_id and message
        """
        try:
            playdate_id = data.get('playdate_id')
            message_content = data.get('message', '').strip()
            
            if not playdate_id:
                emit('error', {'message': 'Playdate ID is required'})
                return
            
            if not message_content:
                emit('error', {'message': 'Message cannot be empty'})
                return
            
            if 'user_id' not in session:
                emit('error', {'message': 'You must be logged in to send messages'})
                return
            
            user_id = session['user_id']
            user = User.query.get(user_id)
            if not user:
                emit('error', {'message': 'User not found'})
                return
            
            # Save message to database
            new_message = PlaydateMessage(
                playdate_id=playdate_id,
                sender_id=user_id,
                content=message_content,
                timestamp=datetime.utcnow()
            )
            
            db.session.add(new_message)
            db.session.commit()
            logger.info(f"New message saved: ID {new_message.id} from User {user.username} to Playdate {playdate_id}")
            
            # Broadcast message to all users in the playdate room
            room = f"playdate_{playdate_id}"
            formatted_message = {
                'id': new_message.id,
                'content': new_message.content,
                'sender_id': user_id,
                'sender_username': user.username,
                'timestamp': new_message.timestamp.isoformat(),
                'formatted_time': new_message.timestamp.strftime('%I:%M %p')
            }
            
            emit('new_message', formatted_message, room=room)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error handling playdate message: {str(e)}")
            emit('error', {'message': 'An error occurred while sending your message'}) 