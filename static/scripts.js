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
    if (timerValue > 0) {
        timerElement.textContent = `Temps restant: ${timerValue}s`;
    } else {
        timerElement.textContent = "Temps écoulé ! :(";
        timerElement.style.color = "#ff6b6b";
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

function showFireworks() {
    const fireworksContainer = document.getElementById('fireworks-container');
    fireworksContainer.innerHTML = '<canvas id="fireworks-canvas"></canvas>';
    const canvas = document.getElementById('fireworks-canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // S'assurer que le canvas reste positionné correctement même avec défilement
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';

    const particles = [];
    const colors = ['#FF1461', '#18FF92', '#5A87FF', '#FBF38C'];

    function createParticle(x, y) {
        const color = colors[Math.floor(Math.random() * colors.length)];
        const particle = {
            x: x,
            y: y,
            radius: Math.random() * 16 + 4, // Augmenter la taille des particules
            color: color,
            speed: Math.random() * 5 + 2,
            angle: Math.random() * 2 * Math.PI,
            alpha: 1,
            decay: Math.random() * 0.03 + 0.01
        };
        particles.push(particle);
    }

    function updateParticles() {
        for (let i = particles.length - 1; i >= 0; i--) {
            const p = particles[i];
            p.x += p.speed * Math.cos(p.angle);
            p.y += p.speed * Math.sin(p.angle);
            p.alpha -= p.decay;
            if (p.alpha <= 0) {
                particles.splice(i, 1);
            }
        }
    }

    function drawParticles() {
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        particles.forEach(p => {
            ctx.globalAlpha = p.alpha;
            ctx.beginPath();
            ctx.arc(p.x, p.y, p.radius, 0, 2 * Math.PI);
            ctx.fillStyle = p.color;
            ctx.fill();
        });
    }

    function loop() {
        updateParticles();
        drawParticles();
        requestAnimationFrame(loop);
    }

    function launchFireworks(x, y) {
        for (let i = 0; i < 100; i++) {
            createParticle(x, y);
        }
    }

    // Lancer des feux d'artifice à différents endroits de l'écran
    launchFireworks(canvas.width / 2, canvas.height / 2); // Centre
    setTimeout(() => launchFireworks(canvas.width / 4, canvas.height / 3), 800); // Gauche-haut
    setTimeout(() => launchFireworks((canvas.width / 4) * 3, canvas.height / 3), 1600); // Droite-haut
    setTimeout(() => launchFireworks(canvas.width / 4, (canvas.height / 3) * 2), 2400); // Gauche-bas
    setTimeout(() => launchFireworks((canvas.width / 4) * 3, (canvas.height / 3) * 2), 3200); // Droite-bas

    loop();
}

function enableNextButton() {
    const nextButton = document.getElementById('next');
    nextButton.disabled = false;
    nextButton.classList.remove('disabled-btn');
    document.getElementById('score-increment').value = correctAnswers;

    // Faire défiler jusqu'au bouton suivant pour s'assurer qu'il est visible
    if (answersCount === 4) {
        nextButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
        showFireworks();
    } else {
        document.body.classList.add('shake');
        setTimeout(() => {
            document.body.classList.remove('shake');
            nextButton.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }, 500);
    }
}

// Fonction pour gérer le redimensionnement de la fenêtre
window.addEventListener('resize', function() {
    const canvas = document.getElementById('fireworks-canvas');
    if (canvas) {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    }
});

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
