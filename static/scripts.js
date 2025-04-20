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

function showFireworks() {
    const fireworksContainer = document.getElementById('fireworks-container');
    fireworksContainer.innerHTML = '<canvas id="fireworks-canvas"></canvas>';
    const canvas = document.getElementById('fireworks-canvas');
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Ensure canvas is positioned correctly even with scrolling
    canvas.style.position = 'fixed';
    canvas.style.top = '0';
    canvas.style.left = '0';
    canvas.style.zIndex = '1000';
    canvas.style.pointerEvents = 'none';

    // Variables to track animation state
    let animationActive = true;
    let rocketTimeouts = [];
    let animationFrameId;

    const particles = [];
    const rockets = [];
    const colors = [
        '#6a11cb', '#2575fc', '#FF1461', '#18FF92', 
        '#5A87FF', '#FBF38C', '#FF4E50', '#FC466B'
    ];

    // Particle class for explosion effects
    class Particle {
        constructor(x, y, color) {
            this.x = x;
            this.y = y;
            this.color = color;
            this.radius = Math.random() * 3 + 2;
            this.speed = Math.random() * 5 + 2;
            this.angle = Math.random() * Math.PI * 2;
            this.friction = 0.95;
            this.gravity = 0.98;
            this.hue = 0;
            this.alpha = 1;
            this.decay = Math.random() * 0.015 + 0.005;
            this.brightness = Math.random() * 50 + 50;
            this.vx = Math.cos(this.angle) * this.speed;
            this.vy = Math.sin(this.angle) * this.speed;
        }

        update() {
            this.vx *= this.friction;
            this.vy *= this.friction;
            this.vy += this.gravity * 0.1;
            this.x += this.vx;
            this.y += this.vy;
            this.alpha -= this.decay;
            return this.alpha <= 0;
        }

        draw() {
            ctx.globalAlpha = this.alpha;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.radius, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.fill();

            // Add glow effect
            ctx.shadowBlur = 15;
            ctx.shadowColor = this.color;
        }
    }

    // Rocket class that launches and explodes
    class Rocket {
        constructor() {
            this.x = Math.random() * canvas.width;
            this.y = canvas.height;
            this.targetX = Math.random() * canvas.width;
            this.targetY = Math.random() * canvas.height / 2;
            this.speed = 2;
            this.angle = Math.atan2(this.targetY - this.y, this.targetX - this.x);
            this.vx = Math.cos(this.angle) * this.speed;
            this.vy = Math.sin(this.angle) * this.speed;
            this.trail = [];
            this.trailLength = 10;
            this.color = colors[Math.floor(Math.random() * colors.length)];
            this.size = 3;
            this.exploded = false;
        }

        update() {
            this.x += this.vx;
            this.y += this.vy;

            // Add trail effect
            this.trail.push({ x: this.x, y: this.y, alpha: 1 });
            if (this.trail.length > this.trailLength) {
                this.trail.shift();
            }

            // Check if rocket reached target
            const distanceToTarget = Math.hypot(this.targetX - this.x, this.targetY - this.y);
            if (distanceToTarget < 15 || this.y < this.targetY) {
                this.explode();
                return true;
            }
            return false;
        }

        draw() {
            // Draw trail
            for (let i = 0; i < this.trail.length; i++) {
                const point = this.trail[i];
                const alpha = i / this.trail.length;
                ctx.globalAlpha = alpha;
                ctx.beginPath();
                ctx.arc(point.x, point.y, this.size, 0, Math.PI * 2);
                ctx.fillStyle = this.color;
                ctx.fill();
            }

            // Draw rocket
            ctx.globalAlpha = 1;
            ctx.beginPath();
            ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
            ctx.fillStyle = this.color;
            ctx.fill();

            // Add glow effect
            ctx.shadowBlur = 10;
            ctx.shadowColor = this.color;
        }

        explode() {
            if (this.exploded) return;
            this.exploded = true;

            // Create explosion particles
            const particleCount = Math.floor(Math.random() * 50) + 50;
            for (let i = 0; i < particleCount; i++) {
                particles.push(new Particle(this.x, this.y, this.color));
            }
        }
    }

    function createRocket() {
        if (!animationActive) return;

        rockets.push(new Rocket());
        // Schedule next rocket and store timeout reference
        const timeout = setTimeout(createRocket, Math.random() * 1000 + 500);
        rocketTimeouts.push(timeout);
    }

    function update() {
        if (!animationActive) return;

        // Clear canvas with semi-transparent black for trail effect
        ctx.fillStyle = 'rgba(0, 0, 0, 0.2)';
        ctx.fillRect(0, 0, canvas.width, canvas.height);

        // Reset shadow
        ctx.shadowBlur = 0;

        // Update and draw rockets
        for (let i = rockets.length - 1; i >= 0; i--) {
            if (rockets[i].update()) {
                rockets.splice(i, 1);
            } else {
                rockets[i].draw();
            }
        }

        // Update and draw particles
        for (let i = particles.length - 1; i >= 0; i--) {
            if (particles[i].update()) {
                particles.splice(i, 1);
            } else {
                particles[i].draw();
            }
        }

        animationFrameId = requestAnimationFrame(update);
    }

    // Function to stop the animation
    function stopAnimation() {
        animationActive = false;

        // Clear all rocket timeouts
        rocketTimeouts.forEach(timeout => clearTimeout(timeout));
        rocketTimeouts = [];

        // Cancel the animation frame
        if (animationFrameId) {
            cancelAnimationFrame(animationFrameId);
        }

        // Clear the canvas completely
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Remove the canvas from DOM
        if (canvas && canvas.parentNode) {
            canvas.parentNode.removeChild(canvas);
        }
    }

    // Start animation
    createRocket();
    update();

    // Create initial fireworks
    for (let i = 0; i < 5; i++) {
        setTimeout(() => rockets.push(new Rocket()), i * 300);
    }

    // Stop the animation after 3 seconds
    setTimeout(stopAnimation, 3000);
}

function enableNextButton() {
    const nextButton = document.getElementById('next');
    nextButton.disabled = false;
    nextButton.classList.remove('disabled-btn');
    document.getElementById('score-increment').value = correctAnswers;

    // Check if we're in reverse mode
    const isReverseMode = document.getElementById('image-choices') !== null;

    // Show fireworks if all answers are correct in normal mode or if the answer is correct in reverse mode
    if (answersCount === 4 || (isReverseMode && document.getElementById('correct-answer').value === "1")) {
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
