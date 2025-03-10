// Initialize map variables
let map;
let markers = [];
let infoWindow;
let currentPosition;
let placesService;
let autocomplete;

// Initialize the map when the page loads
function initMap() {
    // Check if we have a valid API key
    const apiKeyElement = document.getElementById("google-maps-api");
    if (!apiKeyElement) {
        console.error("Missing Google Maps API key element");
        showMapError("Could not initialize map: Missing API key configuration");
        return;
    }
    
    const GOOGLE_MAPS_API_KEY = apiKeyElement.getAttribute("data-key");
    if (!GOOGLE_MAPS_API_KEY || GOOGLE_MAPS_API_KEY === "" || GOOGLE_MAPS_API_KEY === "YOUR_DEFAULT_API_KEY") {
        console.error("Invalid Google Maps API key");
        showMapError("Could not initialize map: Invalid API key");
        return;
    }
    
    // Get the map container
    const mapElement = document.getElementById("map");
    if (!mapElement) {
        console.error("Map container not found");
        return;
    }
    
    // Enable the controls
    const findVenuesButton = document.getElementById("find-venues");
    if (findVenuesButton) {
        findVenuesButton.removeAttribute("disabled");
        // Add event listener for the find venues button
        findVenuesButton.addEventListener("click", findVenues);
    }
    
    const venueTypeSelect = document.getElementById("venue-type");
    if (venueTypeSelect) {
        venueTypeSelect.removeAttribute("disabled");
    }
    
    // Add a class to indicate the map is loaded
    const mapContainer = document.querySelector(".map-container");
    if (mapContainer) {
        mapContainer.classList.add("map-loaded");
    }
    
    // Default to a central location if geolocation is not available
    const defaultLocation = { lat: 40.7128, lng: -74.0060 }; // New York City
    
    // Create the map centered on the default location
    try {
        map = new google.maps.Map(mapElement, {
            center: defaultLocation,
            zoom: 13,
            styles: [
                {
                    "featureType": "poi.business",
                    "stylers": [{ "visibility": "off" }]
                },
                {
                    "featureType": "poi.park",
                    "elementType": "labels.text",
                    "stylers": [{ "visibility": "on" }]
                }
            ]
        });
        
        // Create an info window to share between markers
        infoWindow = new google.maps.InfoWindow();
        
        // Initialize the Places service
        placesService = new google.maps.places.PlacesService(map);
        
        // Initialize the autocomplete for the location input
        initializeAutocomplete();
        
        // Try to get the user's current location
        if (navigator.geolocation) {
            navigator.geolocation.getCurrentPosition(
                (position) => {
                    currentPosition = {
                        lat: position.coords.latitude,
                        lng: position.coords.longitude
                    };
                    
                    // Center the map on the user's location
                    map.setCenter(currentPosition);
                    
                    // Add a marker for the user's location
                    new google.maps.Marker({
                        position: currentPosition,
                        map: map,
                        icon: {
                            path: google.maps.SymbolPath.CIRCLE,
                            scale: 10,
                            fillColor: "#4285F4",
                            fillOpacity: 1,
                            strokeColor: "white",
                            strokeWeight: 2,
                        },
                        title: "Your Location"
                    });
                },
                () => {
                    // Handle geolocation error
                    console.log("Error: The Geolocation service failed.");
                }
            );
        }
    } catch (error) {
        console.error("Error initializing map:", error);
        showMapError("Could not initialize map: " + error.message);
    }
}

// Initialize Google Places Autocomplete for the location input
function initializeAutocomplete() {
    const locationInput = document.getElementById("location");
    if (!locationInput || !google.maps.places.Autocomplete) return;
    
    // Create the autocomplete object
    autocomplete = new google.maps.places.Autocomplete(locationInput, {
        types: ['geocode', 'establishment'],
        fields: ['place_id', 'geometry', 'name', 'formatted_address']
    });
    
    // Bind the autocomplete to the map
    autocomplete.bindTo('bounds', map);
    
    // Add listener for place changed
    autocomplete.addListener('place_changed', function() {
        const place = autocomplete.getPlace();
        
        if (!place.geometry) {
            // User entered the name of a place that was not suggested
            console.log("No details available for: " + place.name);
            return;
        }
        
        // If the place has a geometry, then present it on a map
        if (place.geometry.viewport) {
            map.fitBounds(place.geometry.viewport);
        } else {
            map.setCenter(place.geometry.location);
            map.setZoom(17);
        }
        
        // Clear existing markers
        clearMarkers();
        
        // Add a marker for the selected place
        const marker = new google.maps.Marker({
            position: place.geometry.location,
            map: map,
            animation: google.maps.Animation.DROP,
            title: place.name
        });
        
        markers.push(marker);
    });
}

// Show error message in the map container
function showMapError(message) {
    const mapElement = document.getElementById("map");
    if (mapElement) {
        mapElement.innerHTML = `
            <div class="map-error">
                <i class="fas fa-exclamation-triangle"></i>
                <p>${message}</p>
                <p>Please set up a Google Maps API key in your environment variables.</p>
                <p><small>For development, you can add: export GOOGLE_MAPS_API_KEY=your_api_key</small></p>
            </div>
        `;
        mapElement.classList.add("map-error-container");
    }
}

// Geocode the entered location and update the map
function geocodeLocation(address) {
    if (!map) return;
    
    const geocoder = new google.maps.Geocoder();
    geocoder.geocode({ address: address }, (results, status) => {
        if (status === "OK" && results[0]) {
            map.setCenter(results[0].geometry.location);
            
            // Add a marker for the location
            new google.maps.Marker({
                map: map,
                position: results[0].geometry.location,
                animation: google.maps.Animation.DROP,
                title: address
            });
        } else {
            console.error("Geocode was not successful for the following reason: " + status);
        }
    });
}

// Function to find dog-friendly venues
function findVenues() {
    if (!map || !placesService) {
        console.error("Map or Places service not initialized");
        return;
    }
    
    // Clear existing markers
    clearMarkers();
    
    // Get the venue type from the select element
    const venueTypeSelect = document.getElementById("venue-type");
    const venueType = venueTypeSelect ? venueTypeSelect.value : "dog park";
    
    // Get the current map center
    const center = map.getCenter();
    
    // Show loading indicator in the venue list
    const venueList = document.getElementById("venue-list");
    if (venueList) {
        venueList.innerHTML = '<div class="venue-loading">Searching for venues...</div>';
    }
    
    // Log the search parameters for debugging
    console.log("Searching for venues:", {
        location: center.toJSON(),
        radius: 5000,
        keyword: venueType
    });
    
    // Try a direct search for dog parks first
    placesService.textSearch({
        query: venueType + " near me",
        location: center,
        radius: 10000 // 10km radius for better results
    }, function(results, status) {
        console.log("Text search status:", status, "Results:", results ? results.length : 0);
        
        if (status === google.maps.places.PlacesServiceStatus.OK && results && results.length > 0) {
            displayVenues(results);
        } else {
            // If text search fails, try a nearby search
            placesService.nearbySearch({
                location: center,
                radius: 10000, // 10km radius
                keyword: venueType
            }, function(nearbyResults, nearbyStatus) {
                console.log("Nearby search status:", nearbyStatus, "Results:", nearbyResults ? nearbyResults.length : 0);
                
                if (nearbyStatus === google.maps.places.PlacesServiceStatus.OK && 
                    nearbyResults && nearbyResults.length > 0) {
                    displayVenues(nearbyResults);
                } else {
                    // If both searches fail, show no results message
                    if (venueList) {
                        venueList.innerHTML = `
                            <div class="no-venues">
                                <p>No ${venueType}s found nearby.</p>
                                <p>Try a different search or location.</p>
                                <p><small>You can also enter a location manually in the search box above.</small></p>
                            </div>
                        `;
                    }
                    console.error("All venue searches failed");
                }
            });
        }
    });
}

// Display venues on the map and in the list
function displayVenues(places) {
    console.log("Displaying venues:", places.length);
    
    if (!map || !places || places.length === 0) {
        const venueList = document.getElementById("venue-list");
        if (venueList) {
            venueList.innerHTML = `
                <div class="no-venues">
                    <p>No venues found nearby.</p>
                    <p>Try a different search or location.</p>
                </div>
            `;
        }
        return;
    }
    
    // Clear existing markers
    clearMarkers();
    
    // Get the venue list element
    const venueList = document.getElementById("venue-list");
    if (venueList) {
        venueList.innerHTML = "";
    }
    
    // Create bounds object to contain all markers
    const bounds = new google.maps.LatLngBounds();
    let validPlacesCount = 0;
    
    // Process each place
    places.forEach((place) => {
        if (!place.geometry || !place.geometry.location) {
            console.log("Skipping place without geometry:", place.name);
            return;
        }
        
        validPlacesCount++;
        
        // Extend the bounds to include this place
        bounds.extend(place.geometry.location);
        
        // Create a marker for this place
        const marker = new google.maps.Marker({
            map: map,
            position: place.geometry.location,
            title: place.name,
            animation: google.maps.Animation.DROP
        });
        
        // Add the marker to our array
        markers.push(marker);
        
        // Add click event to the marker
        marker.addListener("click", () => {
            // Get the address from vicinity or formatted_address
            const address = place.vicinity || place.formatted_address || "";
            
            const content = `
                <div class="map-info-window">
                    <h4>${place.name}</h4>
                    <p>${address}</p>
                    ${place.rating ? `<p><i class="fas fa-star"></i> ${place.rating}</p>` : ''}
                    <button class="button small primary select-venue" 
                            data-name="${place.name}" 
                            data-address="${address}">
                        Select this location
                    </button>
                </div>
            `;
            
            infoWindow.setContent(content);
            infoWindow.open(map, marker);
            
            // Add event listener to the select button after the info window is opened
            google.maps.event.addListener(infoWindow, 'domready', () => {
                const selectButton = document.querySelector('.select-venue');
                if (selectButton) {
                    selectButton.addEventListener('click', function() {
                        const venueName = this.getAttribute('data-name');
                        const venueAddress = this.getAttribute('data-address');
                        const locationInput = document.getElementById('location');
                        if (locationInput) {
                            locationInput.value = `${venueName}, ${venueAddress}`;
                        }
                        infoWindow.close();
                    });
                }
            });
        });
        
        // Create a venue item in the list if the venue list exists
        if (venueList) {
            const venueItem = document.createElement("div");
            venueItem.className = "venue-item";
            
            // Get the address from vicinity or formatted_address
            const address = place.vicinity || place.formatted_address || "";
            
            venueItem.innerHTML = `
                <div class="venue-name">${place.name}</div>
                <div class="venue-address">${address}</div>
                ${place.rating ? `
                    <div class="venue-rating">
                        <i class="fas fa-star"></i> ${place.rating}
                    </div>
                ` : ''}
            `;
            
            // Add click event to the venue item
            venueItem.addEventListener("click", () => {
                // Center the map on this venue
                map.setCenter(place.geometry.location);
                map.setZoom(15);
                
                // Open the info window for this venue
                google.maps.event.trigger(marker, "click");
            });
            
            venueList.appendChild(venueItem);
        }
    });
    
    console.log("Valid places displayed:", validPlacesCount);
    
    // If no valid places were found, show a message
    if (validPlacesCount === 0) {
        if (venueList) {
            venueList.innerHTML = `
                <div class="no-venues">
                    <p>No valid venues found nearby.</p>
                    <p>Try a different search or location.</p>
                </div>
            `;
        }
        return;
    }
    
    // Adjust the map bounds to show all markers
    if (markers.length > 0) {
        map.fitBounds(bounds);
    }
}

// Clear all markers from the map
function clearMarkers() {
    markers.forEach(marker => {
        marker.setMap(null);
    });
    markers = [];
}

// Load the Google Maps API
function loadGoogleMapsAPI() {
    const apiKeyElement = document.getElementById("google-maps-api");
    if (!apiKeyElement) {
        console.error("Missing Google Maps API key element");
        showMapError("Missing API key configuration");
        return;
    }
    
    const GOOGLE_MAPS_API_KEY = apiKeyElement.getAttribute("data-key");
    if (!GOOGLE_MAPS_API_KEY || GOOGLE_MAPS_API_KEY === "" || GOOGLE_MAPS_API_KEY === "YOUR_DEFAULT_API_KEY") {
        console.error("Invalid or missing Google Maps API key");
        showMapError("No Google Maps API key provided");
        return;
    }
    
    const script = document.createElement("script");
    script.src = `https://maps.googleapis.com/maps/api/js?key=${GOOGLE_MAPS_API_KEY}&libraries=places&callback=initMap`;
    script.defer = true;
    script.async = true;
    script.onerror = function() {
        console.error("Failed to load Google Maps API");
        showMapError("Failed to load Google Maps API. Check your API key.");
    };
    document.head.appendChild(script);
}

// Add CSS for map error display
const style = document.createElement('style');
style.textContent = `
.map-error-container {
    display: flex;
    align-items: center;
    justify-content: center;
    background-color: #f8f9fa;
    border: 1px solid #dee2e6;
}
.map-error {
    text-align: center;
    padding: 2rem;
    color: #721c24;
}
.map-error i {
    font-size: 3rem;
    margin-bottom: 1rem;
    color: #dc3545;
}
`;
document.head.appendChild(style);

// Load the Google Maps API when the page is loaded
document.addEventListener("DOMContentLoaded", loadGoogleMapsAPI); 