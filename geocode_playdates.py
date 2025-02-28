"""
Script to geocode all existing playdates in the database.
This should be run after adding the latitude and longitude columns to the playdate table.
"""
from app import create_app, db
from app.models.playdate import Playdate
from app.utils.helpers import geocode_address
import time

app = create_app()

def geocode_all_playdates():
    """Geocode all playdates that don't have coordinates"""
    with app.app_context():
        # Get all playdates without coordinates
        playdates = Playdate.query.filter(
            (Playdate.latitude.is_(None)) | (Playdate.longitude.is_(None))
        ).all()
        
        print(f"Found {len(playdates)} playdates to geocode")
        
        success_count = 0
        fail_count = 0
        
        for playdate in playdates:
            print(f"Geocoding playdate {playdate.id}: {playdate.location}")
            
            lat, lng = geocode_address(playdate.location)
            
            if lat and lng:
                playdate.latitude = lat
                playdate.longitude = lng
                success_count += 1
                print(f"  Success: {lat}, {lng}")
            else:
                fail_count += 1
                print(f"  Failed to geocode")
            
            # Sleep briefly to avoid hitting API rate limits
            time.sleep(0.5)
            
            # Commit every 10 playdates to avoid losing all work if there's an error
            if (success_count + fail_count) % 10 == 0:
                db.session.commit()
                print(f"Committed batch of 10 playdates")
        
        # Final commit
        db.session.commit()
        
        print(f"Geocoding complete. Success: {success_count}, Failed: {fail_count}")

if __name__ == "__main__":
    geocode_all_playdates() 