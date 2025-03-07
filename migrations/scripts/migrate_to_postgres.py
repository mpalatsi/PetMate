#!/usr/bin/env python
"""
Script to migrate data from SQLite to PostgreSQL for PetMate application.
This script will:
1. Export data from SQLite database
2. Create tables in PostgreSQL
3. Import data into PostgreSQL

Usage:
    python migrate_to_postgres.py

Requirements:
    - Both SQLite and PostgreSQL databases must be configured
    - Environment variables for PostgreSQL connection must be set
"""

import os
import sys
import json
import sqlite3
import psycopg2
from datetime import datetime
from flask import Flask
from app import create_app, db

def export_sqlite_data(sqlite_path):
    """Export all data from SQLite database to a JSON file."""
    print(f"Exporting data from SQLite database: {sqlite_path}")
    
    # Connect to SQLite database
    conn = sqlite3.connect(sqlite_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()
    
    # Get all table names
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row['name'] for row in cursor.fetchall()]
    
    # Export data from each table
    data = {}
    for table in tables:
        cursor.execute(f"SELECT * FROM {table};")
        rows = cursor.fetchall()
        data[table] = [dict(row) for row in rows]
        print(f"Exported {len(rows)} rows from table {table}")
    
    # Close connection
    conn.close()
    
    # Save data to JSON file
    with open('sqlite_export.json', 'w') as f:
        json.dump(data, f, default=str)
    
    print(f"Data exported to sqlite_export.json")
    return data

def import_to_postgres(data, app):
    """Import data from JSON to PostgreSQL."""
    print("Importing data to PostgreSQL...")
    
    with app.app_context():
        # Create all tables in PostgreSQL
        db.create_all()
        
        # Get table names and their columns
        tables = {}
        for table_name in data.keys():
            # Skip SQLite internal tables
            if table_name.startswith('sqlite_'):
                continue
                
            # Get table model
            if not data[table_name]:
                print(f"Skipping empty table: {table_name}")
                continue
                
            # Get column names from first row
            columns = list(data[table_name][0].keys())
            tables[table_name] = columns
            
        # Import data for each table
        for table_name, columns in tables.items():
            print(f"Importing data to table {table_name}...")
            
            # Skip tables with no data
            if not data[table_name]:
                print(f"No data to import for table {table_name}")
                continue
            
            # Prepare SQL statement
            placeholders = ', '.join(['%s'] * len(columns))
            column_names = ', '.join(columns)
            sql = f"INSERT INTO {table_name} ({column_names}) VALUES ({placeholders})"
            
            # Execute SQL for each row
            with db.engine.connect() as connection:
                for row in data[table_name]:
                    # Extract values in the same order as columns
                    values = [row[column] for column in columns]
                    
                    try:
                        connection.execute(sql, values)
                    except Exception as e:
                        print(f"Error importing row to {table_name}: {e}")
                        print(f"Row data: {row}")
                        continue
                
                # Commit transaction
                connection.commit()
            
            print(f"Imported {len(data[table_name])} rows to table {table_name}")

def main():
    """Main function to run the migration."""
    # Check if environment variables are set
    if not os.environ.get('DATABASE_URL'):
        print("ERROR: DATABASE_URL environment variable is not set.")
        print("Please set the PostgreSQL connection string in the DATABASE_URL environment variable.")
        print("Example: postgresql://username:password@localhost/dbname")
        sys.exit(1)
    
    # Find SQLite database file
    sqlite_path = 'petmate.db'
    if not os.path.exists(sqlite_path):
        sqlite_path = 'instance/petmate.db'
        if not os.path.exists(sqlite_path):
            print("ERROR: SQLite database file not found.")
            print("Please make sure the SQLite database file exists.")
            sys.exit(1)
    
    # Export data from SQLite
    data = export_sqlite_data(sqlite_path)
    
    # Create Flask app with PostgreSQL configuration
    app = create_app()
    
    # Import data to PostgreSQL
    import_to_postgres(data, app)
    
    print("Migration completed successfully!")

if __name__ == '__main__':
    main() 