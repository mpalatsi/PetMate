#!/usr/bin/env python
"""
Diagnostic script to test imports and identify any issues
"""
print("Starting diagnostic tests...")

# First apply monkey patching
print("Applying gevent monkey patching...")
try:
    import gevent.monkey
    gevent.monkey.patch_all()
    print("✓ Successfully applied monkey patching")
except ImportError:
    print("✗ Failed to import gevent")
    exit(1)

# Try importing basic modules
print("\nTesting basic imports...")
try:
    import flask
    print("✓ Flask imported successfully")
    import sqlalchemy
    print("✓ SQLAlchemy imported successfully")
    import eventlet
    print("✓ Eventlet imported successfully")
    import gevent
    print("✓ Gevent imported successfully")
    import gevent.pywsgi
    print("✓ Gevent WSGI imported successfully")
    
    try:
        import geventwebsocket
        print("✓ Gevent WebSocket imported successfully")
    except ImportError:
        print("✗ Failed to import geventwebsocket")
        print("  Try: pip install gevent-websocket")
except ImportError as e:
    print(f"✗ Import error: {e}")

# Test app imports
print("\nTesting app imports...")
try:
    import app
    print("✓ app package imported successfully")
    
    try:
        from app import create_app, socketio
        print("✓ create_app and socketio imported successfully")
        
        try:
            print("\nTrying to create app instance...")
            app_instance = create_app()
            print("✓ App instance created successfully")
        except Exception as e:
            print(f"✗ Failed to create app instance: {e}")
    except Exception as e:
        print(f"✗ Failed to import from app: {e}")
except Exception as e:
    print(f"✗ Failed to import app package: {e}")

print("\nDiagnostic tests completed.") 