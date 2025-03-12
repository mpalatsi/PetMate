"""
Gallery Photos Consistency Checker and Fixer

This script checks for inconsistencies between the database records and actual files
in the gallery photos directory, with options to fix them.

Usage:
    python check_gallery_photos.py [-h] [--fix] [--remove-orphaned-records] [--remove-orphaned-files]

Options:
    --fix                      Automatically fix inconsistencies (default: report only)
    --remove-orphaned-records  Remove database records that don't have corresponding files
    --remove-orphaned-files    Remove files that don't have corresponding database records
"""

import os
import sys
import argparse
from datetime import datetime
from flask import Flask
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Add the current directory to the path so we can import the app
sys.path.append(os.getcwd())

# Create the argument parser
parser = argparse.ArgumentParser(description='Check and fix gallery photos inconsistencies')
parser.add_argument('--fix', action='store_true', help='Automatically fix inconsistencies')
parser.add_argument('--remove-orphaned-records', action='store_true', help='Remove database records without files')
parser.add_argument('--remove-orphaned-files', action='store_true', help='Remove files without database records')
args = parser.parse_args()

# Import the app and models - do this after adding the path
from app import db, create_app
from app.models.gallery_photo import GalleryPhoto

app = create_app()
with app.app_context():
    print("\n=== Gallery Photos Consistency Checker ===")
    print(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Fix mode: {'Enabled' if args.fix else 'Disabled (report only)'}")
    print(f"Remove orphaned records: {'Yes' if args.remove_orphaned_records else 'No'}")
    print(f"Remove orphaned files: {'Yes' if args.remove_orphaned_files else 'No'}")
    
    # Directory where gallery photos should be stored
    gallery_dir = os.path.join('static', 'pet_images', 'gallery_photos')
    print(f"\nGallery directory: {gallery_dir}")
    print(f"Directory exists: {os.path.exists(gallery_dir)}")
    
    if not os.path.exists(gallery_dir):
        print("ERROR: Gallery directory does not exist. Creating it...")
        os.makedirs(gallery_dir, exist_ok=True)
    
    # Get all gallery photos from the database
    db_photos = GalleryPhoto.query.all()
    print(f"\nFound {len(db_photos)} photos in the database")
    
    # Get all files in the gallery directory
    files = []
    if os.path.exists(gallery_dir):
        files = [f for f in os.listdir(gallery_dir) if os.path.isfile(os.path.join(gallery_dir, f))]
    print(f"Found {len(files)} files in the gallery directory")
    
    # Check for database records without files
    db_filenames = [photo.filename for photo in db_photos]
    missing_files = []
    
    print("\n=== Database Records Without Files ===")
    for photo in db_photos:
        file_path = os.path.join(gallery_dir, photo.filename)
        if not os.path.isfile(file_path):
            missing_files.append(photo)
            print(f"ID: {photo.id}, Filename: {photo.filename}, User: {photo.user_id}")
    print(f"Total records without files: {len(missing_files)}")
    
    # Check for files without database records
    orphaned_files = []
    
    print("\n=== Files Without Database Records ===")
    for filename in files:
        if filename not in db_filenames:
            orphaned_files.append(filename)
            file_path = os.path.join(gallery_dir, filename)
            size = os.path.getsize(file_path)
            print(f"Filename: {filename}, Size: {size} bytes")
    print(f"Total orphaned files: {len(orphaned_files)}")
    
    # Perform fixes if requested
    if args.fix:
        print("\n=== Applying Fixes ===")
        
        # Remove orphaned database records if requested
        if args.remove_orphaned_records and missing_files:
            print("\nRemoving orphaned database records...")
            count = 0
            for photo in missing_files:
                try:
                    print(f"Deleting record ID: {photo.id}, Filename: {photo.filename}")
                    db.session.delete(photo)
                    count += 1
                except Exception as e:
                    print(f"Error deleting record: {str(e)}")
            
            print(f"Committing changes... ({count} records)")
            db.session.commit()
            print("Done!")
        
        # Remove orphaned files if requested
        if args.remove_orphaned_files and orphaned_files:
            print("\nRemoving orphaned files...")
            count = 0
            for filename in orphaned_files:
                try:
                    file_path = os.path.join(gallery_dir, filename)
                    print(f"Deleting file: {filename}")
                    os.remove(file_path)
                    count += 1
                except Exception as e:
                    print(f"Error deleting file: {str(e)}")
            
            print(f"Removed {count} orphaned files")
    
    print("\n=== Summary ===")
    print(f"Database records: {len(db_photos)}")
    print(f"Physical files: {len(files)}")
    print(f"Records without files: {len(missing_files)}")
    print(f"Files without records: {len(orphaned_files)}")
    
    if args.fix:
        if args.remove_orphaned_records:
            print(f"Orphaned records removed: {len(missing_files)}")
        if args.remove_orphaned_files:
            print(f"Orphaned files removed: {len(orphaned_files)}")
    else:
        print("\nRun with --fix to apply fixes")
    
    print("\nDone!") 