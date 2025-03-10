# Templates Directory

This directory contains all HTML templates for the PetMate application.

## Note on Consolidation

Previously, templates were stored in two separate locations:
1. `/templates` (root directory)
2. `/app/templates` (app directory)

To resolve confusion and conflicts, all templates have been consolidated into this single location.

## File Organization

- `base.html` - The main base template that all other templates extend
- `mobile_base.html` - Base template for mobile views
- Various feature-specific templates organized by functionality (auth, pets, playdates, etc.)

## Template Rendering

Templates are rendered using Flask's `render_template()` function, which automatically looks in this directory due to the application configuration in `app/__init__.py`:

```python
template_folder = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'templates')
app = Flask(__name__, 
            static_folder=static_folder, 
            static_url_path='/static',
            template_folder=template_folder)
``` 