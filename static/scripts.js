let answersCount = 0;
let correctAnswers = 0;
let currentScore = 0;
let maxScore = 0;
let timerValue = 60;
let timerInterval;

document.addEventListener('DOMContentLoaded', (event) => {
    // Initialize current score and max score if they exist
    const currentScoreElement = document.getElementById('current-score');
    if (currentScoreElement) {
        const scoreText = currentScoreElement.textContent;
        if (scoreText) {
            const scoreParts = scoreText.split(' ');
            if (scoreParts.length >= 5) {
                currentScore = parseInt(scoreParts[2]);
                maxScore = parseInt(scoreParts[4]);
            }
        }
    }

    // Initialize page elements
    const progressBarElement = document.querySelector('.progress-bar-fill');
    const totalQuestionsElement = document.getElementById('total_questions');
    const maxScoreElement = document.getElementById('maxScore');

    if (progressBarElement && totalQuestionsElement && maxScoreElement) {
        const totalQuestions = parseInt(totalQuestionsElement.value);
        const maxScoreValue = parseInt(maxScoreElement.value);
        updateProgressBar(totalQuestions, maxScoreValue / 4);
    }

    // Reset answers count if on game page
    if (document.getElementById('next')) {
        resetAnswersCount();
    }

    // Toggle stats if stats banner exists
    if (document.getElementById('stats-banner')) {
        toggleStats();
    }
});

function checkAnswer(correct, selected, element, currentScoreId, titleId) {
    const buttons = document.querySelectorAll(`#${currentScoreId} button.choice-btn`);
    buttons.forEach(btn => {
        btn.disabled = true;
    });

    if (correct === selected) {
        element.classList.add('correct');
        document.getElementById(titleId).textContent = `${titleId.split('-')[0]}: 1/1`;
        correctAnswers += 1;
        currentScore += 1;
    } else {
        element.classList.add('incorrect');
        buttons.forEach(btn => {
            if (btn.textContent === correct) {
                btn.classList.add('correct');
            }
        });
        document.getElementById(titleId).textContent = `${titleId.split('-')[0]}: 0/1`;
    }

    answersCount += 1;
    document.getElementById('current-score').textContent = `Score actuel : ${currentScore} / ${maxScore}`;

    if (answersCount === 4) {
        enableNextButton();
        clearInterval(timerInterval);
    }
}

function checkImage(correct, selected, element) {
    // Check if we're in reverse mode (with image grid) or normal mode
    const isReverseMode = document.getElementById('image-choices') !== null;
    const buttonSelector = isReverseMode ? '#image-choices .choice-btn' : '.choice-btn';
    const buttons = document.querySelectorAll(buttonSelector);

    buttons.forEach(btn => {
        btn.disabled = true;
        // Add opacity for reverse mode
        if (isReverseMode) {
            btn.style.opacity = "0.6";
        }
    });

    if (correct === selected) {
        element.classList.add('correct');
        correctAnswers += 1;
        currentScore += 1;
        document.getElementById('correct-answer').value = 1;
    } else {
        element.classList.add('incorrect');
        buttons.forEach(btn => {
            if (btn.querySelector('img')?.alt === correct) {
                btn.classList.add('correct');
            }
        });
    }

    // In reverse mode, set answersCount to 1 directly
    if (isReverseMode) {
        answersCount = 1;
        // Use innerHTML for reverse mode to maintain the span
        document.getElementById('current-score').innerHTML = `Score actuel : <span class="score">${currentScore} / ${maxScore}</span>`;
    } else {
        answersCount += 1;
        document.getElementById('current-score').textContent = `Score actuel : ${currentScore} / ${maxScore}`;
    }

    if (answersCount === 1 || (isReverseMode && answersCount === 1)) {
        enableNextButton();
        clearInterval(timerInterval);
    }
}

function updateProgressBar(current, total) {
    const progressBarFill = document.querySelector('.progress-bar-fill');
    const percentage = (current / total) * 100;
    progressBarFill.style.width = percentage + '%';
    progressBarFill.textContent = `${current}/${total}`;
}

function resetAnswersCount() {
    answersCount = 0;
    correctAnswers = 0;
    const nextButton = document.getElementById('next');
    nextButton.disabled = true;
    nextButton.classList.add('disabled-btn');
    startTimer();
}

function startTimer() {
    timerValue = 60;
    updateTimer();
    clearInterval(timerInterval);
    timerInterval = setInterval(function() {
        timerValue--;
        updateTimer();
        if (timerValue <= 0) {
            clearInterval(timerInterval);
            if (answersCount < 4) {
                disableAllButtons();
            }
            enableNextButton();
        }
    }, 1000);
}

function updateTimer() {
    const timerElement = document.getElementById('timer');

    // Remove any existing classes
    timerElement.classList.remove('warning', 'danger');

    if (timerValue > 0) {
        timerElement.textContent = `Temps restant: ${timerValue}s`;

        // Add warning class when time is below 20 seconds
        if (timerValue <= 20 && timerValue > 10) {
            timerElement.classList.add('warning');
        }
        // Add danger class when time is below 10 seconds
        else if (timerValue <= 10) {
            timerElement.classList.add('danger');
        }
    } else {
        timerElement.textContent = "Temps écoulé !";
        timerElement.classList.add('danger');
    }
}

function disableAllButtons() {
    const buttons = document.querySelectorAll('.choice-btn');
    buttons.forEach(btn => {
        if (!btn.classList.contains('correct') && !btn.classList.contains('incorrect')) {
            btn.disabled = true;
            btn.classList.add('disabled-btn');
        }
    });

    enableNextButton();
}

// Fireworks function removed

function enableNextButton() {
    const nextButton = document.getElementById('next');
    nextButton.disabled = false;
    nextButton.classList.remove('disabled-btn');
    document.getElementById('score-increment').value = correctAnswers;

    // Check if we're in reverse mode
    const isReverseMode = document.getElementById('image-choices') !== null;

    if (answersCount === 4 || (isReverseMode && document.getElementById('correct-answer').value === "1")) {
        nextButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
    } else {
        document.body.classList.add('shake');
        setTimeout(() => {
            document.body.classList.remove('shake');
            nextButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 500);
    }
}

// Fireworks resize handler removed

// Function from reverse.html
function toggleStats() {
    const statsBanner = document.getElementById('stats-banner');
    if (statsBanner && (statsBanner.style.display === 'none' || statsBanner.style.display === '')) {
        statsBanner.style.display = 'block';
    } else if (statsBanner) {
        statsBanner.style.display = 'none';
    }
}

// Navigation functions
function goToNormalMode() {
    window.location.href = '/normal';
}

function goToReverseMode() {
    window.location.href = '/reverse';
}

function restartGame() {
    window.location.href = '/restart';
}

// Easter egg - Konami code (up, up, down, down, left, right, left, right, b, a)
let konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'KeyB', 'KeyA'];
let konamiIndex = 0;

// Function to create a visual flash effect when a correct key is pressed
function flashScreen() {
    // Create a flash overlay
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(255, 215, 0, 0.3)'; // Gold color with transparency
    overlay.style.zIndex = '9999';
    overlay.style.pointerEvents = 'none';
    overlay.style.transition = 'opacity 0.3s ease';
    document.body.appendChild(overlay);

    // Remove the overlay after a short delay
    setTimeout(() => {
        overlay.style.opacity = '0';
        setTimeout(() => {
            document.body.removeChild(overlay);
        }, 300);
    }, 100);
}

document.addEventListener('keydown', function(e) {
    // Check if the key pressed matches the next key in the Konami code
    if (e.code === konamiCode[konamiIndex]) {
        // Flash the screen for visual feedback
        flashScreen();

        // Increment the index
        konamiIndex++;

        // If the entire code has been entered correctly
        if (konamiIndex === konamiCode.length) {
            // Reset the index
            konamiIndex = 0;

            // Create a more dramatic effect for the final key
            const finalOverlay = document.createElement('div');
            finalOverlay.style.position = 'fixed';
            finalOverlay.style.top = '0';
            finalOverlay.style.left = '0';
            finalOverlay.style.width = '100%';
            finalOverlay.style.height = '100%';
            finalOverlay.style.backgroundColor = 'rgba(255, 215, 0, 0.7)'; // Brighter gold
            finalOverlay.style.zIndex = '9999';
            finalOverlay.style.pointerEvents = 'none';
            finalOverlay.style.transition = 'opacity 0.5s ease';
            document.body.appendChild(finalOverlay);

            // Redirect after a short delay for the effect to be visible
            setTimeout(() => {
                window.location.href = '/arr';
            }, 500);
        }
    } else {
        // Reset the index if an incorrect key is pressed
        konamiIndex = 0;
    }
});

// Initialize page when loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize progress bar if elements exist
    const progressBarFill = document.querySelector('.progress-bar-fill');
    const totalQuestionsElement = document.getElementById('total-questions');
    const maxScoreElement = document.getElementById('max-score');

    if (progressBarFill && totalQuestionsElement && maxScoreElement) {
        const totalQuestions = parseInt(totalQuestionsElement.value);
        const maxScore = parseInt(maxScoreElement.value);
        updateProgressBar(totalQuestions, maxScore / 4);
    }

    // Reset answers count if on game page
    if (document.getElementById('next')) {
        resetAnswersCount();
    }

    // Toggle stats if on reverse page
    if (document.getElementById('stats-banner')) {
        toggleStats();
    }
});
