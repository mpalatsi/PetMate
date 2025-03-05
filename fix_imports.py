#!/usr/bin/env python
'''
This script removes problematic import statements from main.py that don't exist
in the codebase, specifically pet_sitter, pet_type, appointment, status, notification imports.
'''

def fix_imports():
    print("Fixing imports in main.py...")
    
    # Read the original file
    with open('app/routes/main.py', 'r') as f:
        lines = f.readlines()
    
    # Filter out problematic lines
    filtered_lines = []
    removed_count = 0
    
    for line in lines:
        if any(pattern in line for pattern in [
            'pet_sitter', 'pet_type', 'appointment', 'status', 'notification'
        ]):
            removed_count += 1
            print(f"Removing line: {line.strip()}")
        else:
            filtered_lines.append(line)
    
    # Write the cleaned file
    with open('app/routes/main.py', 'w') as f:
        f.writelines(filtered_lines)
    
    print(f"Finished. Removed {removed_count} import(s).")

if __name__ == "__main__":
    fix_imports() 