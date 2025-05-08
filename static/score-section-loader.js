/**
 * Score Section Loader
 * This script dynamically loads the score section CSS and JS files
 */

document.addEventListener('DOMContentLoaded', function() {
    // Check if the page has a score section
    const scoreSection = document.querySelector('.score-section');
    
    if (scoreSection) {
        // Load the CSS file
        const cssLink = document.createElement('link');
        cssLink.rel = 'stylesheet';
        cssLink.href = '/static/score-section.css';
        document.head.appendChild(cssLink);
        
        // Load the JS file
        const jsScript = document.createElement('script');
        jsScript.src = '/static/score-section.js';
        jsScript.defer = true;
        document.head.appendChild(jsScript);
    }
});