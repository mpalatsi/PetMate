/*
 * PetMate Mobile Enhancements
 * JavaScript for improved mobile experience
 */

document.addEventListener('DOMContentLoaded', function() {
    // Mobile menu improvements
    enhanceMobileMenu();
    
    // Form experience improvements
    enhanceMobileForms();
    
    // Add swipe gestures for common interactions
    addSwipeGestures();
    
    // Add mobile-specific touch enhancements
    addTouchEnhancements();
    
    // Improve responsive image handling
    optimizeImages();
});

/**
 * Enhances the mobile menu experience
 */
function enhanceMobileMenu() {
    // Improve menu toggle animations
    const menuToggle = document.querySelector('.menu-toggle');
    const sliderMenu = document.querySelector('.slider-menu');
    const menuOverlay = document.querySelector('.menu-overlay');
    const closeMenu = document.querySelector('.close-menu');
    
    if (menuToggle && sliderMenu && menuOverlay) {
        // Add smooth transitions for menu
        sliderMenu.style.transition = 'transform 0.3s ease-in-out';
        
        // Prevent body scrolling when menu is open
        menuToggle.addEventListener('click', function() {
            document.body.classList.toggle('menu-open');
            if (document.body.classList.contains('menu-open')) {
                document.body.style.overflow = 'hidden';
            } else {
                document.body.style.overflow = '';
            }
        });
        
        // Close menu function
        function hideMenu() {
            sliderMenu.classList.remove('active');
            menuOverlay.classList.remove('active');
            document.body.classList.remove('menu-open');
            document.body.style.overflow = '';
        }
        
        // Add event listeners for closing menu
        if (closeMenu) {
            closeMenu.addEventListener('click', hideMenu);
        }
        
        menuOverlay.addEventListener('click', hideMenu);
        
        // Close menu when clicking a menu item (for better UX)
        const menuLinks = sliderMenu.querySelectorAll('a:not(.resources-menu-toggle)');
        menuLinks.forEach(link => {
            link.addEventListener('click', hideMenu);
        });
    }
}

/**
 * Enhances form elements for mobile touch
 */
function enhanceMobileForms() {
    // Make date and time inputs more mobile-friendly
    const dateInputs = document.querySelectorAll('input[type="date"]');
    const timeInputs = document.querySelectorAll('input[type="time"]');
    
    // Date inputs need special handling on some mobile devices
    dateInputs.forEach(input => {
        input.addEventListener('focus', function() {
            input.setAttribute('type', 'date');
        });
    });
    
    // Time inputs need special handling on some mobile devices
    timeInputs.forEach(input => {
        input.addEventListener('focus', function() {
            input.setAttribute('type', 'time');
        });
    });
    
    // Enhance mobile form submissions
    const forms = document.querySelectorAll('form');
    forms.forEach(form => {
        form.addEventListener('submit', function() {
            // Add loading state to submit buttons
            const submitButtons = form.querySelectorAll('button[type="submit"], input[type="submit"]');
            submitButtons.forEach(button => {
                button.setAttribute('disabled', 'disabled');
                button.classList.add('loading');
            });
        });
    });
}

/**
 * Adds swipe gesture support for mobile
 */
function addSwipeGestures() {
    // Variables for touch tracking
    let touchStartX = 0;
    let touchEndX = 0;
    let touchStartY = 0;
    let touchEndY = 0;
    
    // Track touch start
    document.addEventListener('touchstart', function(e) {
        touchStartX = e.changedTouches[0].screenX;
        touchStartY = e.changedTouches[0].screenY;
    }, false);
    
    // Track touch end
    document.addEventListener('touchend', function(e) {
        touchEndX = e.changedTouches[0].screenX;
        touchEndY = e.changedTouches[0].screenY;
        handleSwipe();
    }, false);
    
    // Handle swipe gesture
    function handleSwipe() {
        // Calculate horizontal distance
        const horizontalDist = touchEndX - touchStartX;
        // Calculate vertical distance
        const verticalDist = touchEndY - touchStartY;
        
        // Only trigger if horizontal swipe is significant and not a vertical scroll
        if (Math.abs(horizontalDist) > 100 && Math.abs(verticalDist) < 50) {
            // Right to left swipe
            if (horizontalDist < 0) {
                // Open menu if swiping from left edge
                if (touchStartX < 30) {
                    const menuToggle = document.querySelector('.menu-toggle');
                    if (menuToggle) {
                        menuToggle.click();
                    }
                }
            }
            // Left to right swipe
            else {
                // Close menu if open
                const sliderMenu = document.querySelector('.slider-menu.active');
                if (sliderMenu) {
                    const closeMenu = document.querySelector('.close-menu');
                    if (closeMenu) {
                        closeMenu.click();
                    }
                }
            }
        }
    }
}

/**
 * Adds mobile-specific touch enhancements
 */
function addTouchEnhancements() {
    // Add active state for buttons
    const buttons = document.querySelectorAll('button, .button, .cta-button, .submit-button');
    
    buttons.forEach(button => {
        button.addEventListener('touchstart', function() {
            button.classList.add('touch-active');
        });
        
        button.addEventListener('touchend', function() {
            button.classList.remove('touch-active');
        });
        
        button.addEventListener('touchcancel', function() {
            button.classList.remove('touch-active');
        });
    });
}

/**
 * Optimizes images for better mobile loading
 */
function optimizeImages() {
    // Only run this on mobile devices
    if (window.innerWidth <= 768) {
        // Delay loading non-essential images
        const nonEssentialImages = document.querySelectorAll('.pet-image:not(.essential), .gallery-image:not(.essential)');
        
        // Create intersection observer for lazy loading
        if ('IntersectionObserver' in window) {
            const imageObserver = new IntersectionObserver((entries, observer) => {
                entries.forEach(entry => {
                    if (entry.isIntersecting) {
                        const img = entry.target;
                        const dataSrc = img.getAttribute('data-src');
                        
                        if (dataSrc) {
                            img.src = dataSrc;
                            img.removeAttribute('data-src');
                        }
                        
                        imageObserver.unobserve(img);
                    }
                });
            });
            
            nonEssentialImages.forEach(img => {
                imageObserver.observe(img);
            });
        }
        // Fallback for browsers without intersection observer
        else {
            nonEssentialImages.forEach(img => {
                const dataSrc = img.getAttribute('data-src');
                if (dataSrc) {
                    img.src = dataSrc;
                    img.removeAttribute('data-src');
                }
            });
        }
    }
} 