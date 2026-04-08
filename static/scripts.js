// scripts.js - Thin aliases to GameEngine (game-engine.js).
// Templates call these global functions; they delegate directly to GameEngine.
// NO duplicate state, NO sync -- GameEngine is the single source of truth.

// --------------- Game function aliases ---------------

function checkAnswer(correct, selected, element, currentScoreId, titleId) {
    GameEngine.checkAnswer(correct, selected, element, currentScoreId, titleId);
}

function checkImage(correct, selected, element) {
    GameEngine.checkImage(correct, selected, element);
}

function updateProgressBar(current, total) {
    GameEngine.updateProgressBar(current, total);
}

function resetAnswersCount() {
    GameEngine.resetAnswersCount();
}

function startTimer(seconds) {
    GameEngine.startTimer(seconds || 60);
}

function updateTimer() {
    GameEngine.updateTimer();
}

function disableAllButtons(container) {
    GameEngine.disableAllButtons(container);
}

function enableNextButton() {
    GameEngine.enableNextButton();
}

function createConfetti(element) {
    GameEngine.createConfetti(element);
}

function toggleStats() {
    GameEngine.toggleStats();
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
    overlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(255,215,0,0.3);z-index:9999;pointer-events:none;transition:opacity 0.3s ease';
    document.body.appendChild(overlay);
    setTimeout(function() {
        overlay.style.opacity = '0';
        setTimeout(function() { document.body.removeChild(overlay); }, 300);
    }, 100);
}

document.addEventListener('keydown', function(e) {
    if (e.code === konamiCode[konamiIndex]) {
        flashScreen();
        konamiIndex++;
        if (konamiIndex === konamiCode.length) {
            konamiIndex = 0;
            var finalOverlay = document.createElement('div');
            finalOverlay.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(255,215,0,0.7);z-index:9999;pointer-events:none;transition:opacity 0.5s ease';
            document.body.appendChild(finalOverlay);
            setTimeout(function() { window.location.href = '/arr'; }, 500);
        }
    } else {
        konamiIndex = 0;
    }
});

// --------------- Init ---------------

document.addEventListener('DOMContentLoaded', function() {
    GameEngine.init();

    // Load optional enhancement scripts
    var fireworksScript = document.createElement('script');
    fireworksScript.src = '/static/fireworks-responsive.js';
    fireworksScript.defer = true;
    document.head.appendChild(fireworksScript);

    var animationsScript = document.createElement('script');
    animationsScript.src = '/static/animations.js';
    animationsScript.defer = true;
    document.head.appendChild(animationsScript);
});
