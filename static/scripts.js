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

    // Don't toggle stats on load to keep them hidden by default
    // if (document.getElementById('stats-banner')) {
    //     toggleStats();
    // }

    // Dynamically load animations.js
    const animationsScript = document.createElement('script');
    animationsScript.src = '/static/animations.js';
    animationsScript.defer = true;
    document.head.appendChild(animationsScript);

    // Load test script in development mode
    // This can be removed in production
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        const testScript = document.createElement('script');
        testScript.src = '/static/test.js';
        testScript.defer = true;
        document.head.appendChild(testScript);
        console.log('Test mode enabled. Check console for test results.');
    }
});

function checkAnswer(correct, selected, element, currentScoreId, titleId) {
    // Add a subtle animation to the selected element before showing result
    element.classList.add('processing');

    // Delay the result to create anticipation
    setTimeout(() => {
        // Remove processing class
        element.classList.remove('processing');

        // Disable all buttons in this category
        const buttons = document.querySelectorAll(`#${currentScoreId} button.choice-btn`);
        buttons.forEach(btn => {
            btn.disabled = true;
            btn.classList.add('disabled-btn');
        });

        // Check if answer is correct
        if (correct === selected) {
            // Correct answer animation and updates
            element.classList.add('correct');
            element.classList.remove('disabled-btn');

            // Update title with success icon
            document.getElementById(titleId).innerHTML = `${titleId.split('-')[0]}: <span class="success-icon">✓</span> 1/1`;

            // Update scores
            correctAnswers += 1;
            currentScore += 1;

            // Add confetti effect for correct answer
            createConfetti(element);
        } else {
            // Incorrect answer animation and updates
            element.classList.add('incorrect');

            // Highlight the correct answer
            buttons.forEach(btn => {
                if (btn.textContent === correct) {
                    btn.classList.add('correct');
                    btn.classList.remove('disabled-btn');
                }
            });

            // Update title with error icon
            document.getElementById(titleId).innerHTML = `${titleId.split('-')[0]}: <span class="error-icon">✗</span> 0/1`;
        }

        // Update the score display with animation
        const scoreElement = document.getElementById('current-score');
        scoreElement.classList.add('score-updated');
        scoreElement.textContent = `Score actuel : ${currentScore} / ${maxScore}`;

        // Remove animation class after animation completes
        setTimeout(() => {
            scoreElement.classList.remove('score-updated');
        }, 1000);

        // Check if all questions are answered
        answersCount += 1;
        if (answersCount === 4) {
            enableNextButton();
            clearInterval(timerInterval);
        }
    }, 300); // 300ms delay for anticipation
}

// Function to create confetti effect
function createConfetti(element) {
    // Get element position
    const rect = element.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;

    // Create confetti container if it doesn't exist
    let confettiContainer = document.getElementById('confetti-container');
    if (!confettiContainer) {
        confettiContainer = document.createElement('div');
        confettiContainer.id = 'confetti-container';
        confettiContainer.style.position = 'fixed';
        confettiContainer.style.top = '0';
        confettiContainer.style.left = '0';
        confettiContainer.style.width = '100%';
        confettiContainer.style.height = '100%';
        confettiContainer.style.pointerEvents = 'none';
        confettiContainer.style.zIndex = '9999';
        document.body.appendChild(confettiContainer);
    }

    // Create confetti particles
    const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff'];

    for (let i = 0; i < 30; i++) {
        const confetti = document.createElement('div');
        confetti.style.position = 'absolute';
        confetti.style.width = '10px';
        confetti.style.height = '10px';
        confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        confetti.style.borderRadius = '50%';
        confetti.style.left = `${centerX}px`;
        confetti.style.top = `${centerY}px`;
        confetti.style.transform = 'translate(-50%, -50%)';
        confetti.style.opacity = '1';
        confetti.style.transition = 'all 1s ease-out';

        confettiContainer.appendChild(confetti);

        // Animate confetti
        setTimeout(() => {
            const angle = Math.random() * Math.PI * 2;
            const distance = 50 + Math.random() * 100;
            confetti.style.left = `${centerX + Math.cos(angle) * distance}px`;
            confetti.style.top = `${centerY + Math.sin(angle) * distance}px`;
            confetti.style.opacity = '0';
        }, 10);

        // Remove confetti after animation
        setTimeout(() => {
            confettiContainer.removeChild(confetti);
        }, 1000);
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

    // Ensure current is at least 1 to make the progress bar visible at the beginning
    const displayCurrent = Math.max(1, current);

    // Ensure minimum width for visibility (10% at the beginning)
    const percentage = (displayCurrent / total) * 100;
    progressBarFill.style.width = Math.max(10, percentage) + '%';

    // Make sure the text is visible by using a contrasting color and larger font
    progressBarFill.style.color = 'white';
    progressBarFill.style.fontWeight = 'bold';
    progressBarFill.style.textShadow = '1px 1px 2px rgba(0, 0, 0, 0.7)';

    // Display the current progress
    progressBarFill.textContent = `${displayCurrent}/${Math.round(total)}`;
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

    // Determine if we should show confetti based on game mode and success
    let showConfetti = false;

    if (isReverseMode) {
        // In reverse mode, show confetti if the answer was correct
        showConfetti = document.getElementById('correct-answer').value === "1";
    } else {
        // In normal mode, show confetti if all answers are correct
        showConfetti = correctAnswers === 4;
    }

    // For other game modes, only show confetti if there was at least one correct answer
    if (!isReverseMode && !document.querySelector('.normal-choices')) {
        showConfetti = correctAnswers > 0;
    }

    // Create confetti effect for successful completions
    if (showConfetti) {
        // Create confetti at the center of the screen
        const centerX = window.innerWidth / 2;
        const centerY = window.innerHeight / 2;

        // Create confetti container if it doesn't exist
        let confettiContainer = document.getElementById('confetti-container');
        if (!confettiContainer) {
            confettiContainer = document.createElement('div');
            confettiContainer.id = 'confetti-container';
            confettiContainer.style.position = 'fixed';
            confettiContainer.style.top = '0';
            confettiContainer.style.left = '0';
            confettiContainer.style.width = '100%';
            confettiContainer.style.height = '100%';
            confettiContainer.style.pointerEvents = 'none';
            confettiContainer.style.zIndex = '9999';
            document.body.appendChild(confettiContainer);
        }

        // Create more confetti for a bigger celebration
        const colors = ['#ff0000', '#00ff00', '#0000ff', '#ffff00', '#ff00ff', '#00ffff'];

        for (let i = 0; i < 100; i++) {
            const confetti = document.createElement('div');
            confetti.style.position = 'absolute';
            confetti.style.width = '10px';
            confetti.style.height = '10px';
            confetti.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
            confetti.style.borderRadius = Math.random() > 0.5 ? '50%' : '0';
            confetti.style.left = `${centerX}px`;
            confetti.style.top = `${centerY}px`;
            confetti.style.transform = 'translate(-50%, -50%)';
            confetti.style.opacity = '1';
            confetti.style.transition = 'all 1.5s ease-out';

            confettiContainer.appendChild(confetti);

            // Animate confetti
            setTimeout(() => {
                const angle = Math.random() * Math.PI * 2;
                const distance = 100 + Math.random() * 200;
                confetti.style.left = `${centerX + Math.cos(angle) * distance}px`;
                confetti.style.top = `${centerY + Math.sin(angle) * distance}px`;
                confetti.style.opacity = '0';
                confetti.style.transform = `translate(-50%, -50%) rotate(${Math.random() * 360}deg)`;
            }, 10);

            // Remove confetti after animation
            setTimeout(() => {
                if (confettiContainer.contains(confetti)) {
                    confettiContainer.removeChild(confetti);
                }
            }, 1500);
        }
    } else {
        // Only add shake effect if confetti is not shown
        document.body.classList.add('shake');
        setTimeout(() => {
            document.body.classList.remove('shake');
        }, 500);
    }

    // Always scroll to the next button
    nextButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
}

// Fireworks resize handler removed

// Track if the page has just loaded
let pageJustLoaded = true;

// Function from reverse.html
function toggleStats() {
    const statsBanner = document.getElementById('stats-banner');
    const toggleButton = document.querySelector('.toggle-stats-btn');

    if (statsBanner) {
        // If page just loaded, keep stats hidden and update flag
        if (pageJustLoaded) {
            pageJustLoaded = false;
            statsBanner.style.display = 'none';
            if (toggleButton) {
                toggleButton.textContent = 'Afficher les statistiques';
            }
            return;
        }

        // Toggle the display
        if (statsBanner.style.display === 'block') {
            statsBanner.style.display = 'none';
            if (toggleButton) {
                toggleButton.textContent = 'Afficher les statistiques';
            }
        } else {
            statsBanner.style.display = 'block';
            if (toggleButton) {
                toggleButton.textContent = 'Masquer les statistiques';
            }
        }
    }
}

// Initialize stats panel to be hidden by default
document.addEventListener('DOMContentLoaded', function() {
    const statsBanner = document.getElementById('stats-banner');
    const toggleButton = document.querySelector('.toggle-stats-btn');

    if (statsBanner) {
        statsBanner.style.display = 'none';
        if (toggleButton) {
            toggleButton.textContent = 'Afficher les statistiques';
        }
    }
});

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

    // Don't toggle stats on load to keep them hidden by default
    // if (document.getElementById('stats-banner')) {
    //     toggleStats();
    // }
});
