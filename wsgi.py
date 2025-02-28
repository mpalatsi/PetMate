#!/usr/bin/env python
"""
WSGI server script for running the application with gevent and websockets.
This provides proper WebSocket support using gevent-websocket.
"""
# Apply gevent monkey patching
from gevent import monkey
monkey.patch_all(thread=False)

import logging
import os
from gevent.pywsgi import WSGIServer
from geventwebsocket.handler import WebSocketHandler
from app import create_app, socketio

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create the Flask application
app = create_app()

def run_server():
    """Run the application with gevent's WSGIServer using WebSocketHandler."""
    logger.info("Starting gevent server with WebSocket support...")
    
    # Development mode (default)
    port = int(os.environ.get('PORT', 5002))
    host = os.environ.get('HOST', '0.0.0.0')
    
    # Check if we're in debug mode
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ('true', '1', 't')
    app.debug = debug
    
    if debug:
        # Use Flask's development server with SocketIO
        logger.info(f"Running in development mode on http://{host}:{port}")
        socketio.run(
            app,
            host=host,
            port=port,
            debug=True,
            use_reloader=True,
            log_output=True
        )
    else:
        # Use production WSGI server
        logger.info(f"Running in production mode on http://{host}:{port}")
        http_server = WSGIServer(
            (host, port),
            app,
            handler_class=WebSocketHandler,
            log=logger
        )
        try:
            http_server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Server shutting down...")
            http_server.stop()

if __name__ == '__main__':
    run_server() 