// Test script to verify that the application is functioning properly
console.log('Running test script...');

// Function to test if an element exists and has the expected properties
function testElement(selector, expectedProperties = {}) {
    const element = document.querySelector(selector);
    if (!element) {
        console.error(`Element not found: ${selector}`);
        return false;
    }
    
    console.log(`Element found: ${selector}`);
    
    // Check if the element has the expected properties
    for (const [property, expectedValue] of Object.entries(expectedProperties)) {
        const actualValue = window.getComputedStyle(element)[property];
        if (actualValue !== expectedValue) {
            console.warn(`Property mismatch for ${selector}.${property}: expected ${expectedValue}, got ${actualValue}`);
        } else {
            console.log(`Property match for ${selector}.${property}: ${actualValue}`);
        }
    }
    
    return true;
}

// Function to test if animations are working
function testAnimations() {
    // Check if animations.js was loaded
    const animationsScript = document.querySelector('script[src="/static/animations.js"]');
    if (!animationsScript) {
        console.error('animations.js was not loaded');
        return false;
    }
    
    console.log('animations.js was loaded successfully');
    
    // Check if fade-in animation was applied to main layout
    const mainLayout = document.querySelector('.main-layout');
    if (mainLayout && !mainLayout.classList.contains('fade-in')) {
        console.warn('fade-in class was not applied to main layout');
    } else if (mainLayout) {
        console.log('fade-in class was applied to main layout');
    }
    
    // Check if profile-image class was applied to employee photos
    const employeeImages = document.querySelectorAll('img[alt="Photo d\'employé"]');
    let profileImageApplied = true;
    employeeImages.forEach(img => {
        if (!img.classList.contains('profile-image')) {
            console.warn('profile-image class was not applied to employee photo');
            profileImageApplied = false;
        }
    });
    
    if (profileImageApplied && employeeImages.length > 0) {
        console.log('profile-image class was applied to all employee photos');
    }
    
    return true;
}

// Run tests when the page is fully loaded
document.addEventListener('DOMContentLoaded', function() {
    // Wait a bit to ensure animations.js has time to run
    setTimeout(() => {
        console.log('Running tests...');
        
        // Test basic elements
        testElement('body', { 'fontFamily': 'var(--font-primary)' });
        testElement('.main-layout');
        testElement('.center-content');
        testElement('.right-content');
        
        // Test animations
        testAnimations();
        
        console.log('Tests completed.');
    }, 500);
});

// Add a visual indicator that tests are running
const testIndicator = document.createElement('div');
testIndicator.style.position = 'fixed';
testIndicator.style.bottom = '10px';
testIndicator.style.left = '10px';
testIndicator.style.padding = '5px 10px';
testIndicator.style.backgroundColor = 'rgba(0, 0, 0, 0.7)';
testIndicator.style.color = 'white';
testIndicator.style.borderRadius = '5px';
testIndicator.style.fontSize = '12px';
testIndicator.style.zIndex = '9999';
testIndicator.textContent = 'Running tests...';
document.body.appendChild(testIndicator);

// Update the indicator when tests are complete
setTimeout(() => {
    testIndicator.textContent = 'Tests completed. Check console for results.';
    testIndicator.style.backgroundColor = 'rgba(0, 128, 0, 0.7)';
    
    // Remove the indicator after a few seconds
    setTimeout(() => {
        document.body.removeChild(testIndicator);
    }, 5000);
}, 1000);