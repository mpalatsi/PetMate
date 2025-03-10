#!/usr/bin/env python
"""
Update Gallery URLs Script

This script updates all templates to use the gallery.index route instead of main.gallery.
It recursively searches through all HTML files in the app/templates directory
and replaces "url_for('main.gallery')" with "url_for('gallery.index')".

Usage:
    python scripts/update_gallery_urls.py
"""

import os
import re
from pathlib import Path

def update_gallery_urls(templates_dir='app/templates'):
    """Updates all templates to use gallery.index instead of main.gallery"""
    pattern = re.compile(r"url_for\('main\.gallery'\)")
    replacement = "url_for('gallery.index')"
    
    # Count files updated and occurrences replaced
    files_updated = 0
    occurrences_replaced = 0
    
    # Walk through all HTML files in the templates directory
    for root, _, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html'):
                file_path = os.path.join(root, file)
                
                # Read the file content
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Check if the pattern exists in the file
                matches = pattern.findall(content)
                if matches:
                    # Replace the pattern
                    updated_content = pattern.sub(replacement, content)
                    
                    # Write the updated content back to the file
                    with open(file_path, 'w', encoding='utf-8') as f:
                        f.write(updated_content)
                    
                    files_updated += 1
                    occurrences_replaced += len(matches)
                    print(f"Updated {file_path}: {len(matches)} occurrences")
    
    print(f"\nSummary: Updated {files_updated} files with {occurrences_replaced} replacements")
    return files_updated, occurrences_replaced

if __name__ == "__main__":
    print("Updating gallery URLs in templates...")
    update_gallery_urls()
    print("Done!") 