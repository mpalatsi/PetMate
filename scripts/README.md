# PetMate Utility Scripts

This directory contains utility scripts for the PetMate project that help with development, maintenance, and troubleshooting.

## Setup

Install the required dependencies:

```bash
pip install -r requirements-scripts.txt
```

## Available Scripts

### Server Management (`manage_server.py`)

This script helps with starting, stopping, and managing the Flask server on port 5006.

```bash
# Check server status
python scripts/manage_server.py check

# Start the server
python scripts/manage_server.py start

# Stop the server
python scripts/manage_server.py stop

# Restart the server (stop and then start)
python scripts/manage_server.py restart

# Force stop the server without confirmation
python scripts/manage_server.py stop --force
```

### Template Checker (`check_templates.py`)

This script scans Flask templates for common issues, including undefined variables and inconsistencies between mobile and desktop versions.

```bash
# Check all templates
python scripts/check_templates.py

# Check templates in a specific directory
python scripts/check_templates.py --path admin

# Try to automatically fix common issues
python scripts/check_templates.py --fix-common-issues
```

The script identifies:
- References to undefined variables
- Inconsistencies between mobile and desktop template versions
- Templates that exist in one format but not the other

## When to Use

- **Before Running**: Use `manage_server.py check` to see if there's already a server running on port 5006
- **When Port Conflict Occurs**: Use `manage_server.py stop` to kill the process using port 5006
- **After Template Changes**: Use `check_templates.py` to verify that you haven't introduced template errors
- **When Getting Template Errors**: Use `check_templates.py --fix-common-issues` to try automatic fixes

## Adding New Scripts

When adding new utility scripts to this directory:

1. Follow the same structure as existing scripts
2. Add proper documentation with usage examples
3. Update this README with information about the new script
4. Add any new dependencies to `requirements-scripts.txt` 