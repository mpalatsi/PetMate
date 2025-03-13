/**
 * PetMate Mobile Detector
 * Detects mobile devices and redirects to the mobile-optimized homepage
 */

document.addEventListener('DOMContentLoaded', function() {
    // First check if we're on the homepage
    const isHomepage = window.location.pathname === '/' || 
                       window.location.pathname === '/index' || 
                       window.location.pathname.endsWith('/index.html');
    
    // Check if we're on the gallery page
    const isGallery = window.location.pathname === '/gallery' ||
                      window.location.pathname.startsWith('/gallery');
    
    // Only redirect if we're on the homepage and not already on the mobile version
    if (isHomepage && !window.location.pathname.includes('mobile')) {
        // Simple mobile detection - can be enhanced if needed
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent) || 
                         window.innerWidth < 768;
        
        if (isMobile) {
            // Check if user has manually chosen to view desktop version
            if (localStorage.getItem('preferMobileVersion') !== 'false') {
                // Store preference in localStorage
                localStorage.setItem('preferMobileVersion', 'true');
                
                // Redirect to mobile version
                window.location.href = '/mobile';
            }
        }
    }
    
    // Add event listeners for view switching if those elements exist
    const viewDesktopButton = document.getElementById('view-desktop-version');
    const viewMobileButton = document.getElementById('view-mobile-version');
    
    if (viewDesktopButton) {
        viewDesktopButton.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.setItem('preferMobileVersion', 'false');
            
            // If on mobile gallery, redirect to desktop gallery
            if (window.location.pathname === '/mobile-gallery' || 
                window.location.pathname.includes('/gallery') && window.location.search.includes('mobile=true')) {
                window.location.href = '/gallery';
            } else {
                window.location.href = '/';
            }
        });
    }
    
    if (viewMobileButton) {
        viewMobileButton.addEventListener('click', function(e) {
            e.preventDefault();
            localStorage.setItem('preferMobileVersion', 'true');
            
            // If on gallery page, redirect to mobile gallery
            if (isGallery) {
                window.location.href = '/mobile-gallery';
            } else {
                window.location.href = '/mobile';
            }
        });
    }
});

// Add a simple function to force mobile or desktop view
function switchToView(viewType) {
    if (viewType === 'mobile') {
        localStorage.setItem('preferMobileVersion', 'true');
        
        // If on gallery page, redirect to mobile gallery
        if (window.location.pathname === '/gallery' || 
            window.location.pathname.startsWith('/gallery')) {
            window.location.href = '/mobile-gallery';
        } else {
            window.location.href = '/mobile';
        }
    } else {
        localStorage.setItem('preferMobileVersion', 'false');
        
        // If on mobile gallery, redirect to desktop gallery
        if (window.location.pathname === '/mobile-gallery') {
            window.location.href = '/gallery';
        } else {
            window.location.href = '/';
        }
    }
} 