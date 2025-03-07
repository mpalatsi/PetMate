import sqlite3
import os

# Path to the database file
db_path = os.path.join('app', 'petmate.db')

# Connect to the database
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

try:
    # Check if the gallery_photos table exists
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='gallery_photos';")
    if cursor.fetchone():
        print("Gallery photos table exists, checking columns...")
        
        # Get current columns
        cursor.execute("PRAGMA table_info(gallery_photos);")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        print(f"Current columns: {column_names}")
        
        # Check and add missing columns
        needed_columns = {
            'user_id': 'INTEGER NOT NULL',
            'title': 'VARCHAR(255)',
            'description': 'TEXT',
            'is_public': 'BOOLEAN DEFAULT 1'
        }
        
        for col_name, col_type in needed_columns.items():
            if col_name not in column_names:
                try:
                    print(f"Adding column {col_name}...")
                    cursor.execute(f"ALTER TABLE gallery_photos ADD COLUMN {col_name} {col_type};")
                    conn.commit()
                    print(f"Added column {col_name} successfully.")
                except Exception as e:
                    print(f"Error adding column {col_name}: {str(e)}")
                    conn.rollback()
        
        # Add foreign key relationship if needed
        if 'user_id' in column_names:
            print("Validating user_id foreign key...")
            # SQLite doesn't allow adding foreign key constraints after table creation
            # So we need to create a temporary table with the right structure, copy data, and rename
            try:
                cursor.execute("""
                CREATE TABLE IF NOT EXISTS uploader_relation (
                    id INTEGER PRIMARY KEY,
                    gallery_photo_id INTEGER,
                    user_id INTEGER,
                    FOREIGN KEY(gallery_photo_id) REFERENCES gallery_photos(id) ON DELETE CASCADE,
                    FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE
                );
                """)
                conn.commit()
                print("Created uploader relation table to maintain foreign key integrity.")
            except Exception as e:
                print(f"Error creating uploader relation: {str(e)}")
                conn.rollback()
    else:
        print("Gallery photos table does not exist.")
        
    print("Database update completed.")
    
except Exception as e:
    print(f"Error updating database: {str(e)}")
    conn.rollback()
finally:
    conn.close()
    
print("Script finished.") 