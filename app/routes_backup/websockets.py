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
        logger.info(f"WEBSOCKET: Client connected: {request.sid} - User: {session.get('username', 'Anonymous')}")
        print(f"WEBSOCKET: Client connected: {request.sid} - User: {session.get('username', 'Anonymous')}")
        emit('connection_response', {'status': 'connected', 'sid': request.sid})
    
    @socketio.on('disconnect')
    def handle_disconnect():
        """Handle client disconnection"""
        logger.info(f"WEBSOCKET: Client disconnected: {request.sid} - User: {session.get('username', 'Anonymous')}")
        print(f"WEBSOCKET: Client disconnected: {request.sid} - User: {session.get('username', 'Anonymous')}")
    
    @socketio.on('join_playdate_room')
    def handle_join_playdate_room(data):
        """
        Handle client joining a playdate chat room
        
        Args:
            data: Dictionary containing playdate_id
        """
        logger.info(f"WEBSOCKET: Join room request received: {data}")
        print(f"WEBSOCKET: Join room request received: {data}")
        
        playdate_id = data.get('playdate_id')
        if not playdate_id:
            logger.error("WEBSOCKET: No playdate_id in join request")
            emit('error', {'message': 'Playdate ID is required'})
            return
        
        if 'username' not in session:
            logger.error(f"WEBSOCKET: No username in session. Session data: {session}")
            emit('error', {'message': 'You must be logged in to join a playdate chat'})
            return
        
        user = User.query.filter_by(username=session['username']).first()
        if not user:
            logger.error(f"WEBSOCKET: User not found for username: {session.get('username')}")
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
        messages = PlaydateMessage.query.filter_by(playdate_id=playdate_id).order_by(PlaydateMessage.created_at).all()
        
        # Send history to the user
        formatted_messages = []
        for msg in messages:
            sender = User.query.get(msg.sender_id)
            formatted_messages.append({
                'id': msg.id,
                'content': msg.content,
                'sender_id': msg.sender_id,
                'sender_username': sender.username if sender else 'Unknown',
                'timestamp': msg.created_at.isoformat(),
                'formatted_time': msg.created_at.strftime('%I:%M %p')
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
        
        if 'username' not in session:
            return
        
        user = User.query.filter_by(username=session['username']).first()
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
            print(f"Message received: {data}")
            logger.info(f"WEBSOCKET: Received message data: {data}")
            
            playdate_id = data.get('playdate_id')
            message_content = data.get('message', '').strip()
            
            if not playdate_id:
                logger.error("WEBSOCKET: Playdate ID is missing")
                emit('error', {'message': 'Playdate ID is required'})
                return
            
            if not message_content:
                logger.error("WEBSOCKET: Message content is empty")
                emit('error', {'message': 'Message cannot be empty'})
                return
            
            if 'username' not in session:
                logger.error(f"WEBSOCKET: No username in session. Session data: {session}")
                emit('error', {'message': 'You must be logged in to send messages'})
                return
            
            user = User.query.filter_by(username=session['username']).first()
            if not user:
                logger.error(f"WEBSOCKET: User not found for username: {session.get('username')}")
                emit('error', {'message': 'User not found'})
                return
            
            logger.info(f"WEBSOCKET: Creating message from {user.username} for playdate {playdate_id}")
            
            # Save message to database
            new_message = PlaydateMessage(
                playdate_id=playdate_id,
                sender_id=user.id,
                content=message_content
            )
            
            db.session.add(new_message)
            db.session.commit()
            logger.info(f"WEBSOCKET: New message saved: ID {new_message.id} from User {user.username} to Playdate {playdate_id}")
            
            # Broadcast message to all users in the playdate room
            room = f"playdate_{playdate_id}"
            formatted_message = {
                'id': new_message.id,
                'content': new_message.content,
                'sender_id': user.id,
                'sender_username': user.username,
                'timestamp': new_message.created_at.isoformat(),
                'formatted_time': new_message.created_at.strftime('%I:%M %p'),
                'created_at': new_message.created_at.isoformat()  # Adding created_at for consistency
            }
            
            logger.info(f"WEBSOCKET: Broadcasting message to room {room}: {formatted_message}")
            emit('new_message', formatted_message, room=room)
            
        except Exception as e:
            db.session.rollback()
            logger.error(f"WEBSOCKET ERROR: {str(e)}")
            logger.exception("WEBSOCKET Exception details:")
            emit('error', {'message': 'An error occurred while sending your message'}) 