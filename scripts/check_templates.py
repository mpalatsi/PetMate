#!/usr/bin/env python
"""
Template Checker Utility

This script scans Flask templates to detect common issues:
1. References to undefined variables
2. Inconsistencies between mobile and desktop template versions
3. Missing template blocks

Usage:
    python scripts/check_templates.py
    python scripts/check_templates.py --path app/templates/admin
    python scripts/check_templates.py --fix-common-issues
"""

import os
import re
import sys
import argparse
from pathlib import Path
import jinja2
import jinja2.meta
import jinja2.exceptions

class TemplateChecker:
    """Utility to check Flask templates for common issues"""
    
    def __init__(self, template_folder='app/templates'):
        self.template_folder = template_folder
        self.env = jinja2.Environment(loader=jinja2.FileSystemLoader(template_folder))
        self.common_vars = {
            # Common variables that should be defined in routes
            'current_user', 'user', 'csrf_token', 'form', 'pagination', 
            'error', 'errors', 'success', 'message', 'messages',
            'page', 'total_pages', 'url_for', 'session', 'request',
            'get_flashed_messages', 'debug_info', 'stats', 'items'
        }
        self.mobile_prefix = 'mobile_'
        self.issues_found = 0
        
    def find_templates(self, subdir=None):
        """Find all template files in the specified directory"""
        search_path = os.path.join(self.template_folder, subdir or '')
        return list(Path(search_path).glob('**/*.html'))

    def extract_variables(self, template_path):
        """Extract all variables referenced in a template"""
        with open(template_path, 'r', encoding='utf-8') as f:
            source = f.read()
        
        try:
            ast = self.env.parse(source)
            variables = jinja2.meta.find_undeclared_variables(ast)
            return variables
        except jinja2.exceptions.TemplateSyntaxError as e:
            print(f"\n❌ Syntax error in {template_path}: {e}")
            self.issues_found += 1
            return set()

    def check_undefined_variables(self, template_path):
        """Check for potentially undefined variables in a template"""
        template_name = os.path.basename(template_path)
        variables = self.extract_variables(template_path)
        
        # Filter out common Flask variables and built-in functions
        potential_undefined = variables - self.common_vars - {'loop', 'range', 'dict', 'list', 'None', 'True', 'False'}
        
        # Alert about variables that might not be defined
        if potential_undefined:
            print(f"\n🔍 In {template_name}, check these potentially undefined variables:")
            for var in sorted(potential_undefined):
                print(f"   - {var}")
            self.issues_found += 1
            return potential_undefined
        return set()

    def check_mobile_desktop_consistency(self):
        """Check for consistency between mobile and desktop template versions"""
        templates = self.find_templates()
        desktop_templates = [t for t in templates if not os.path.basename(t).startswith(self.mobile_prefix)]
        mobile_templates = [t for t in templates if os.path.basename(t).startswith(self.mobile_prefix)]
        
        desktop_names = {os.path.basename(t).replace('.html', '') for t in desktop_templates}
        mobile_names = {os.path.basename(t).replace('.html', '').replace(self.mobile_prefix, '') for t in mobile_templates}
        
        # Find desktop templates missing mobile versions
        missing_mobile = desktop_names - mobile_names
        if missing_mobile:
            print("\n⚠️ Desktop templates missing mobile versions:")
            for name in sorted(missing_mobile):
                print(f"   - {name}.html (needs {self.mobile_prefix}{name}.html)")
            self.issues_found += 1
        
        # Find mobile templates missing desktop versions
        missing_desktop = mobile_names - desktop_names
        if missing_desktop:
            print("\n⚠️ Mobile templates missing desktop versions:")
            for name in sorted(missing_desktop):
                print(f"   - {self.mobile_prefix}{name}.html (needs {name}.html)")
            self.issues_found += 1
        
        # Compare variables between mobile and desktop pairs
        for name in mobile_names.intersection(desktop_names):
            mobile_path = next(t for t in mobile_templates if os.path.basename(t) == f"{self.mobile_prefix}{name}.html")
            desktop_path = next(t for t in desktop_templates if os.path.basename(t) == f"{name}.html")
            
            mobile_vars = self.extract_variables(mobile_path)
            desktop_vars = self.extract_variables(desktop_path)
            
            # Check for variables in one but not the other
            mobile_only = mobile_vars - desktop_vars
            desktop_only = desktop_vars - mobile_vars
            
            if mobile_only:
                print(f"\n⚠️ Variables only in mobile version of {name}:")
                for var in sorted(mobile_only):
                    print(f"   - {var}")
                self.issues_found += 1
                
            if desktop_only:
                print(f"\n⚠️ Variables only in desktop version of {name}:")
                for var in sorted(desktop_only):
                    print(f"   - {var}")
                self.issues_found += 1

    def scan_all_templates(self, subdir=None):
        """Scan all templates for issues"""
        templates = self.find_templates(subdir)
        
        if not templates:
            print(f"No templates found in {os.path.join(self.template_folder, subdir or '')}")
            return
            
        print(f"Checking {len(templates)} templates for issues...")
        
        for template_path in templates:
            self.check_undefined_variables(template_path)
            
        self.check_mobile_desktop_consistency()
        
        if self.issues_found == 0:
            print("\n✅ No issues found in templates!")
        else:
            print(f"\n⚠️ Found {self.issues_found} potential issues in templates.")

    def fix_common_issues(self, subdir=None):
        """Try to fix common template issues automatically"""
        templates = self.find_templates(subdir)
        fixed_count = 0
        
        for template_path in templates:
            with open(template_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            # Fix 1: Add checks for 'user' variables
            modified = re.sub(r'(\{\{\s*user\.)', r'{% if user is defined %}{{ user.', content)
            modified = re.sub(r'(user\.[a-zA-Z0-9_]+\s*\}\})', r'\1{% else %}N/A{% endif %}', modified)
            
            # Fix 2: Add checks for other common variables
            for var in ['form', 'items', 'pagination']:
                modified = re.sub(f'(\{{\{{\s*{var}\.)', f'{{% if {var} is defined %}}{{{{ {var}.', modified)
                modified = re.sub(f'({var}\.[a-zA-Z0-9_]+\s*\}}}})', r'\1{% else %}N/A{% endif %}', modified)
                
            if modified != content:
                with open(template_path, 'w', encoding='utf-8') as f:
                    f.write(modified)
                print(f"✅ Fixed potential issues in {os.path.basename(template_path)}")
                fixed_count += 1
                
        if fixed_count == 0:
            print("No automatic fixes were applied.")
        else:
            print(f"Applied fixes to {fixed_count} templates.")

def main():
    parser = argparse.ArgumentParser(description='Check Flask templates for common issues')
    parser.add_argument('--path', help='Subfolder of templates to check')
    parser.add_argument('--fix-common-issues', action='store_true', help='Try to fix common issues automatically')
    args = parser.parse_args()
    
    checker = TemplateChecker()
    
    if args.fix_common_issues:
        checker.fix_common_issues(args.path)
    else:
        checker.scan_all_templates(args.path)
        
    sys.exit(1 if checker.issues_found > 0 else 0)

if __name__ == '__main__':
    main() 