# PetMate - Restructured Flask Application

## New Project Structure

The PetMate application has been restructured from a single file application to a more maintainable package structure. Here's an overview of the new structure:

```
PetMate/
├── app/                      # Main application package
│   ├── __init__.py           # Application factory
│   ├── models/               # Database models
│   │   ├── __init__.py
│   │   ├── associations.py   # Association tables
│   │   ├── user.py           # User model
│   │   ├── pet.py            # Pet model
│   │   ├── playdate.py       # Playdate model
│   │   ├── message.py        # Message model
│   │   ├── review.py         # Review model
│   │   └── photo.py          # PlaydatePhoto and GalleryPhoto models
│   ├── routes/               # Route handlers
│   │   ├── __init__.py
│   │   ├── main.py           # Main routes (index, dashboard)
│   │   ├── auth.py           # Authentication routes
│   │   ├── pets.py           # Pet management routes
│   │   ├── playdates.py      # Playdate routes
│   │   ├── messages.py       # Messaging routes
│   │   └── profiles.py       # User profile routes
│   ├── static/               # Static files
│   ├── templates/            # Templates
│   └── utils/                # Helper functions
│       ├── __init__.py
│       └── helpers.py        # Utility functions
├── config.py                 # Configuration
├── run.py                    # Entry point
└── requirements.txt          # Dependencies
```

## Why This Structure?

This new structure provides several benefits:

1. **Separation of Concerns**: Each part of the application has its own logical place
2. **Maintainability**: Smaller files are easier to understand and modify
3. **Scalability**: New features can be added without cluttering existing files
4. **Testability**: Components can be tested in isolation
5. **Collaboration**: Multiple developers can work on different parts with fewer conflicts

## How to Run the Application

1. Make sure you're in the root directory (PetMate)
2. Run the application using:
   ```
   python run.py
   ```

3. The application will be available at http://localhost:5000

## Migration Notes

The application has been restructured, but it still uses the same database and maintains all functionality of the original application. The database schema and table names remain unchanged, so existing databases are compatible.

## Development Guidelines

When adding new features:

1. **New Models**: Add to the `app/models/` directory
2. **New Routes**: Add to the `app/routes/` directory, using blueprints
3. **Helper Functions**: Add to `app/utils/helpers.py`
4. **Config Changes**: Modify the `config.py` file

## Unit Testing

A testing structure will be added in the future to enable proper unit testing of individual components. 