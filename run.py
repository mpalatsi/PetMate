from app import create_app, db

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        # Create tables if they don't exist 
        try:
            db.create_all()
        except Exception as e:
            # Just log the error and continue
            print(f"Note: {e}")
    
    app.run(debug=True) 