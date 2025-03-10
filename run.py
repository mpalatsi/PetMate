from app import create_app, db, socketio

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist 
        try:
            db.create_all()
        except Exception as e:
            # Just log the error and continue
            print(f"Note: {e}")
    
    # Run with explicit host and port to avoid binding issues
    # and ensure WebSockets are accessible from all interfaces
    socketio.run(app, host='0.0.0.0', port=5006, debug=True, allow_unsafe_werkzeug=True) 