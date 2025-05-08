// JavaScript for the normal game mode redesign

document.addEventListener('DOMContentLoaded', function() {
    // Make sure stats are hidden by default
    const statsBanner = document.getElementById('stats-banner');
    if (statsBanner) {
        statsBanner.style.display = 'none';
    }

    // Initialize the sequential display of game parts
    initializeSequentialDisplay();
});

// Global variables to track the current part and state
let currentPart = 0;
const parts = ['company', 'team', 'name', 'position'];
let partCompleted = [false, false, false, false];

function initializeSequentialDisplay() {
    // Get all game parts
    const gameParts = document.querySelectorAll('.game-section > div');
    
    // Hide all parts initially
    gameParts.forEach(part => {
        part.classList.remove('active');
    });
    
    // Show only the first part
    showGamePart(0);
    
    // Override the checkAnswer function to handle sequential display
    const originalCheckAnswer = window.checkAnswer;
    window.checkAnswer = function(correct, selected, element, currentScoreId, titleId) {
        // Call the original function first
        originalCheckAnswer(correct, selected, element, currentScoreId, titleId);
        
        // Get the current part index
        const partIndex = parts.indexOf(titleId.split('-')[0]);
        
        // Mark this part as completed
        partCompleted[partIndex] = true;
        
        // Move to the next part after a short delay
        setTimeout(() => {
            if (partIndex < parts.length - 1) {
                showGamePart(partIndex + 1);
            }
        }, 1000);
    };
}

function showGamePart(index) {
    // Update the current part index
    currentPart = index;
    
    // Get all game parts
    const gameParts = document.querySelectorAll('.game-section > div');
    
    // Hide all parts
    gameParts.forEach(part => {
        part.classList.remove('active');
    });
    
    // Show only the current part
    if (index < gameParts.length) {
        gameParts[index].classList.add('active');
        gameParts[index].classList.add('slide-in');
        
        // Focus on the first button of this part
        setTimeout(() => {
            const firstButton = gameParts[index].querySelector('button');
            if (firstButton) {
                firstButton.focus();
            }
        }, 100);
    }
}

// Override the enableNextButton function to reset the sequential display
const originalEnableNextButton = window.enableNextButton;
if (originalEnableNextButton) {
    window.enableNextButton = function() {
        // Call the original function
        originalEnableNextButton();
        
        // Reset the part completion state for the next question
        partCompleted = [false, false, false, false];
    };
}

// Override the resetAnswersCount function to reset the sequential display
const originalResetAnswersCount = window.resetAnswersCount;
if (originalResetAnswersCount) {
    window.resetAnswersCount = function() {
        // Call the original function
        originalResetAnswersCount();
        
        // Reset the sequential display
        initializeSequentialDisplay();
    };
}