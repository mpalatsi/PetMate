# Static Files

This directory contains all static files for the PetMate application.

## Folder Structure

- `css/` - CSS files for specific components
- `js/` - JavaScript files
- `images/` - General images
- `profile_pictures/` - User profile pictures
- `pet_images/` - Pet images
- `playdate_photos/` - Photos from playdates
- `gallery/` - Gallery photos

## Note on Consolidation

This static folder was created by consolidating two separate static folders:
1. `/static` (root directory)
2. `/app/static` (app directory)

The consolidation was done to resolve issues with having two separate static folders in the production environment.

## File References

All templates should reference static files using the Flask `url_for` function:

```html
<link rel="stylesheet" href="{{ url_for('static', filename='style.css') }}">
<img src="{{ url_for('static', filename='profile_pictures/' + user.profile_picture) }}">
```

## File Upload Paths

When uploading files, make sure to use the correct path for saving files. Files should be saved to the `uploads` directory, not the `static` directory. 