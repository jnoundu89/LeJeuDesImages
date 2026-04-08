// JavaScript for the normal game mode redesign
// Handles sequential display of game parts (company -> team -> name -> position)

document.addEventListener('DOMContentLoaded', function() {
    // Make sure stats are hidden by default
    var statsBanner = document.getElementById('stats-banner');
    if (statsBanner) {
        statsBanner.style.display = 'none';
    }

    // Initialize the sequential display of game parts
    initializeSequentialDisplay();
});

// Global variables to track the current part and state
var currentPart = 0;
var parts = ['company', 'team', 'name', 'position'];
var partCompleted = [false, false, false, false];

function initializeSequentialDisplay() {
    // Get all game parts
    var gameParts = document.querySelectorAll('.game-section > div');

    // Hide all parts initially
    gameParts.forEach(function(part) {
        part.classList.remove('active');
    });

    // Show only the first part
    showGamePart(0);

    // Override checkAnswer to handle sequential display
    var originalCheckAnswer = window.checkAnswer;
    window.checkAnswer = function(correct, selected, element, currentScoreId, titleId) {
        // Call the original function first
        originalCheckAnswer(correct, selected, element, currentScoreId, titleId);

        // Get the current part index
        var partIndex = parts.indexOf(titleId.split('-')[0]);

        // Mark this part as completed
        partCompleted[partIndex] = true;

        // Move to the next part after a short delay
        setTimeout(function() {
            if (partIndex < parts.length - 1) {
                showGamePart(partIndex + 1);
            }
        }, 1000);
    };
}

function showGamePart(index) {
    currentPart = index;

    var gameParts = document.querySelectorAll('.game-section > div');

    gameParts.forEach(function(part) {
        part.classList.remove('active');
    });

    if (index < gameParts.length) {
        gameParts[index].classList.add('active');
        gameParts[index].classList.add('slide-in');

        setTimeout(function() {
            var firstButton = gameParts[index].querySelector('button');
            if (firstButton) {
                firstButton.focus();
            }
        }, 100);
    }
}

// Override enableNextButton to reset sequential display
var originalEnableNextButton = window.enableNextButton;
if (originalEnableNextButton) {
    window.enableNextButton = function() {
        originalEnableNextButton();
        partCompleted = [false, false, false, false];
    };
}

// Override resetAnswersCount to reset sequential display
var originalResetAnswersCount = window.resetAnswersCount;
if (originalResetAnswersCount) {
    window.resetAnswersCount = function() {
        originalResetAnswersCount();
        initializeSequentialDisplay();
    };
}
