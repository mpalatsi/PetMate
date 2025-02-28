# PetMate Location Search Upgrade Instructions

This document provides step-by-step instructions for upgrading the PetMate application with improved location-based search functionality.

## Overview of Changes

The upgrades include:
1. Adding latitude and longitude fields to the Playdate model
2. Adding geocoding functionality to convert addresses/zipcodes to coordinates
3. Updating the location search to use actual distance calculations
4. Enhancing the playdate creation/editing to automatically geocode locations

## Prerequisites

✅ The Google Maps API key is already set up in your .env file. No action required for this step.

If you ever need to change the API key, you can update it in the .env file:
```
GOOGLE_MAPS_API_KEY=your_api_key_here
```

## Installation Steps

### Option 1: Automated Upgrade (Recommended)

We've created a batch file that will handle the entire upgrade process for you:

1. Simply run the batch file:
   ```
   upgrade_location_search.bat
   ```

2. After the upgrade completes, restart your application:
   ```
   python run.py
   ```

### Option 2: Manual Upgrade Steps

If you prefer to run the steps manually, follow these instructions:

1. **Update dependencies**
   
   Install the new required package:
   ```
   pip install -r requirements.txt
   ```

2. **Apply database migrations**
   
   Run the migration script to add the new columns:
   ```
   python migrate.py
   ```

3. **Geocode existing playdates**
   
   Run the script to geocode all existing playdates:
   ```
   python geocode_playdates.py
   ```

4. **Restart the application**
   ```
   python run.py
   ```

## New Features

### Improved Search Functionality

- **Distance-based search**: Searches now return playdates within the specified distance radius
- **Sorting by distance**: Results can be sorted by proximity to the search location
- **Better zipcode support**: Searches by zipcode now properly match nearby locations

### Creating and Editing Playdates

- Locations are now automatically geocoded when playdates are created or edited
- This enables accurate distance calculations in the search feature

## Troubleshooting

- If geocoding fails, ensure your Google Maps API key is correctly set in the .env file
- If the API key is correct but geocoding still fails, check that the Geocoding API is enabled in your Google Cloud Console
- For any database migration issues, you may need to manually run the SQL commands in the migrate.py file

## Future Improvements

- Display a map with playdate locations
- Add a "find nearest" button to show playdates closest to the user's current location
- Implement radius-based filtering on the map view 