#!/usr/bin/env python
# Import gevent and monkey patch
from gevent import monkey
monkey.patch_all()

# Standard library imports
import os
import sys
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
logger.info("Initializing application with gevent monkey patching")

# Now import Flask and extensions
from app import create_app, db, socketio
from app.models.user import User
from app.models.pet import Pet

# Create app
app = create_app()

@app.shell_context_processor
def make_shell_context():
    """Add database and models to flask shell context"""
    return {'db': db, 'User': User, 'Pet': Pet}

if __name__ == '__main__':
    # Use gevent WSGI server via Flask-SocketIO
    logger.info("Starting Socket.IO server with gevent")
    socketio.run(
        app,
        debug=True,
        port=5001,
        host='0.0.0.0'
    ) 