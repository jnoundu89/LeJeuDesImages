// scripts.js - Thin wrapper that delegates to GameEngine (game-engine.js)
// and exposes global functions for backwards compatibility with templates.

// Global state variables kept for any external code that reads them directly.
// GameEngine owns the authoritative state; these are synced as needed.
var answersCount = 0;
var correctAnswers = 0;
var currentScore = 0;
var maxScore = 0;
var timerValue = 60;
var timerInterval;

// --------------- Sync helpers ---------------

function _syncFromEngine() {
    if (typeof GameEngine === 'undefined') return;
    var s = GameEngine.getState();
    answersCount = s.answersCount;
    correctAnswers = s.correctAnswers;
    currentScore = s.currentScore;
    maxScore = s.maxScore;
    timerValue = s.timerValue;
}

function _syncToEngine() {
    if (typeof GameEngine === 'undefined') return;
    GameEngine.setState('answersCount', answersCount);
    GameEngine.setState('correctAnswers', correctAnswers);
    GameEngine.setState('currentScore', currentScore);
    GameEngine.setState('maxScore', maxScore);
    GameEngine.setState('timerValue', timerValue);
}

// --------------- Global functions (backwards-compatible) ---------------

function checkAnswer(correct, selected, element, currentScoreId, titleId) {
    if (typeof GameEngine !== 'undefined') {
        _syncToEngine();
        GameEngine.checkAnswer(correct, selected, element, currentScoreId, titleId);
        _syncFromEngine();
    }
}

function checkImage(correct, selected, element) {
    if (typeof GameEngine !== 'undefined') {
        _syncToEngine();
        GameEngine.checkImage(correct, selected, element);
        _syncFromEngine();
    }
}

function updateProgressBar(current, total) {
    if (typeof GameEngine !== 'undefined') {
        GameEngine.updateProgressBar(current, total);
    }
}

function resetAnswersCount() {
    if (typeof GameEngine !== 'undefined') {
        GameEngine.resetAnswersCount();
        _syncFromEngine();
    }
}

function startTimer(seconds) {
    if (typeof GameEngine !== 'undefined') {
        GameEngine.startTimer(seconds || 60);
    }
}

function updateTimer() {
    if (typeof GameEngine !== 'undefined') {
        GameEngine.updateTimer();
    }
}

function disableAllButtons(container) {
    if (typeof GameEngine !== 'undefined') {
        _syncToEngine();
        GameEngine.disableAllButtons(container);
        _syncFromEngine();
    }
}

function enableNextButton() {
    if (typeof GameEngine !== 'undefined') {
        _syncToEngine();
        GameEngine.enableNextButton();
        _syncFromEngine();
    }
}

function createConfetti(element) {
    if (typeof GameEngine !== 'undefined') {
        GameEngine.createConfetti(element);
    }
}

function toggleStats() {
    if (typeof GameEngine !== 'undefined') {
        GameEngine.toggleStats();
    }
}

// --------------- Navigation functions ---------------

function goToNormalMode() {
    window.location.href = '/normal';
}

function goToReverseMode() {
    window.location.href = '/reverse';
}

function restartGame() {
    window.location.href = '/restart';
}

// --------------- Easter egg - Konami code ---------------

var konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'KeyB', 'KeyA'];
var konamiIndex = 0;

function flashScreen() {
    var overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(255, 215, 0, 0.3)';
    overlay.style.zIndex = '9999';
    overlay.style.pointerEvents = 'none';
    overlay.style.transition = 'opacity 0.3s ease';
    document.body.appendChild(overlay);

    setTimeout(function() {
        overlay.style.opacity = '0';
        setTimeout(function() {
            document.body.removeChild(overlay);
        }, 300);
    }, 100);
}

document.addEventListener('keydown', function(e) {
    if (e.code === konamiCode[konamiIndex]) {
        flashScreen();
        konamiIndex++;

        if (konamiIndex === konamiCode.length) {
            konamiIndex = 0;

            var finalOverlay = document.createElement('div');
            finalOverlay.style.position = 'fixed';
            finalOverlay.style.top = '0';
            finalOverlay.style.left = '0';
            finalOverlay.style.width = '100%';
            finalOverlay.style.height = '100%';
            finalOverlay.style.backgroundColor = 'rgba(255, 215, 0, 0.7)';
            finalOverlay.style.zIndex = '9999';
            finalOverlay.style.pointerEvents = 'none';
            finalOverlay.style.transition = 'opacity 0.5s ease';
            document.body.appendChild(finalOverlay);

            setTimeout(function() {
                window.location.href = '/arr';
            }, 500);
        }
    } else {
        konamiIndex = 0;
    }
});

// --------------- Single DOMContentLoaded listener ---------------

document.addEventListener('DOMContentLoaded', function() {
    // Initialize GameEngine if available
    if (typeof GameEngine !== 'undefined') {
        GameEngine.init();
        _syncFromEngine();
    }

    // Load fireworks responsive script
    var fireworksScript = document.createElement('script');
    fireworksScript.src = '/static/fireworks-responsive.js';
    fireworksScript.defer = true;
    document.head.appendChild(fireworksScript);

    // Load animations script
    var animationsScript = document.createElement('script');
    animationsScript.src = '/static/animations.js';
    animationsScript.defer = true;
    document.head.appendChild(animationsScript);
});
