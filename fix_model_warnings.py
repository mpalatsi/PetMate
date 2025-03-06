#!/usr/bin/env python
"""
Script to find and list model files that need to be updated to fix SQLAlchemy relationship warnings.
"""
import os
import sys
import glob

def find_model_files():
    """Find all Python model files in the app/models directory."""
    model_files = []
    pattern = os.path.join('app', 'models', '*.py')
    model_files.extend(glob.glob(pattern))
    
    # Check subdirectories if any
    pattern = os.path.join('app', 'models', '**', '*.py')
    model_files.extend(glob.glob(pattern, recursive=True))
    
    return model_files

def check_relationship_definitions(file_path):
    """Check if a file contains SQLAlchemy relationship definitions that may need the overlaps parameter."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Look for relationships of interest
    needs_review = False
    relationships = []
    
    if 'Playdate.host' in content and 'relationship(' in content:
        relationships.append("Playdate.host needs overlaps='hosted_playdates'")
        needs_review = True
    
    if 'Playdate.attendees' in content and 'relationship(' in content:
        relationships.append("Playdate.attendees needs overlaps='attended_playdates'")
        needs_review = True
    
    if 'User.hosted_playdates' in content and 'relationship(' in content:
        relationships.append("User.hosted_playdates needs overlaps='host'")
        needs_review = True
    
    if 'User.attended_playdates' in content and 'relationship(' in content:
        relationships.append("User.attended_playdates needs overlaps='attendees'")
        needs_review = True
    
    return needs_review, relationships

def main():
    """Main function to run the script."""
    print("Checking model files for SQLAlchemy relationship warnings...")
    
    model_files = find_model_files()
    if not model_files:
        print("No model files found. Make sure you're running this script from the project root directory.")
        sys.exit(1)
    
    files_to_fix = []
    for file_path in model_files:
        needs_review, relationships = check_relationship_definitions(file_path)
        if needs_review:
            files_to_fix.append((file_path, relationships))
    
    if not files_to_fix:
        print("No files found that need fixing.")
    else:
        print("Files that need to be updated:")
        for file_path, relationships in files_to_fix:
            print(f"\n{file_path}:")
            for rel in relationships:
                print(f"  - {rel}")
        
        print("\nTo fix these warnings, add the overlaps parameter to the relationship definitions.")
        print("For example, change:")
        print("    relationship('User', backref='hosted_playdates')")
        print("To:")
        print("    relationship('User', backref='hosted_playdates', overlaps='host')")

if __name__ == '__main__':
    main() 