// homepage.js - Enhanced interactions for the homepage

document.addEventListener('DOMContentLoaded', function() {
    // Initialize animations
    initAnimations();

    // Initialize mode cards interaction
    initModeCards();

    // Initialize particle background
    initParticleBackground();

    // Initialize typing effect
    initTypingEffect();

    // Initialize Easter egg
    initKonamiCode();
});

// Initialize animations for various elements
function initAnimations() {
    // Add fade-in animation to header
    const header = document.querySelector('.game-header');
    if (header) {
        header.classList.add('fade-in');
    }

    // Add staggered fade-in to mode cards
    const modeGrid = document.querySelector('.mode-grid');
    if (modeGrid) {
        modeGrid.classList.add('stagger-fade-in');
    }

    // Add float animation to the logo
    const logo = document.querySelector('.game-logo');
    if (logo) {
        logo.classList.add('float');
    }

    // Add pulse animation to the play buttons
    const playButtons = document.querySelectorAll('.mode-button');
    playButtons.forEach(button => {
        button.classList.add('pulse');
    });
}

// Initialize mode cards interaction
function initModeCards() {
    const modeCards = document.querySelectorAll('.mode-card');

    modeCards.forEach(card => {
        // Add hover effect class
        card.classList.add('card-hover');

        // Add shine effect
        card.classList.add('shine');

        // Add click effect
        card.addEventListener('click', function(e) {
            // Don't trigger if clicking on the button
            if (e.target.classList.contains('mode-button')) return;

            // Find the button in this card and click it
            const button = this.querySelector('.mode-button');
            if (button) {
                // Add jello animation before clicking
                this.classList.add('jello');

                // Remove the animation after it completes
                setTimeout(() => {
                    this.classList.remove('jello');
                    button.click();
                }, 500);
            }
        });
    });
}

// Initialize particle background
function initParticleBackground() {
    const canvas = document.getElementById('particles-canvas');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');

    // Set canvas size
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;

    // Particle settings
    const particleCount = 100;
    const particles = [];
    const colors = [
        'rgba(255, 215, 0, 0.7)',  // Gold
        'rgba(63, 81, 181, 0.5)',  // Primary
        'rgba(0, 150, 136, 0.5)',  // Secondary
        'rgba(255, 255, 255, 0.5)' // White
    ];

    // Create particles
    for (let i = 0; i < particleCount; i++) {
        particles.push({
            x: Math.random() * canvas.width,
            y: Math.random() * canvas.height,
            radius: Math.random() * 3 + 1,
            color: colors[Math.floor(Math.random() * colors.length)],
            speedX: Math.random() * 0.5 - 0.25,
            speedY: Math.random() * 0.5 - 0.25
        });
    }

    // Animation loop
    function animate() {
        requestAnimationFrame(animate);

        // Clear canvas
        ctx.clearRect(0, 0, canvas.width, canvas.height);

        // Update and draw particles
        particles.forEach(particle => {
            // Move particle
            particle.x += particle.speedX;
            particle.y += particle.speedY;

            // Wrap around edges
            if (particle.x < 0) particle.x = canvas.width;
            if (particle.x > canvas.width) particle.x = 0;
            if (particle.y < 0) particle.y = canvas.height;
            if (particle.y > canvas.height) particle.y = 0;

            // Draw particle
            ctx.beginPath();
            ctx.arc(particle.x, particle.y, particle.radius, 0, Math.PI * 2);
            ctx.fillStyle = particle.color;
            ctx.fill();
        });
    }

    // Start animation
    animate();

    // Handle window resize
    window.addEventListener('resize', function() {
        canvas.width = window.innerWidth;
        canvas.height = window.innerHeight;
    });
}

// Initialize typing effect for the tagline
function initTypingEffect() {
    // We're disabling the typing effect to ensure the text displays correctly
    // and is fully visible without going off-screen
    const tagline = document.querySelector('.game-tagline');
    if (!tagline) return;

    // Instead of the typing effect, we'll just add a fade-in animation
    tagline.classList.add('fade-in');
}

// Initialize Konami Code Easter egg
function initKonamiCode() {
    const konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'b', 'a'];
    let konamiIndex = 0;

    document.addEventListener('keydown', function(e) {
        // Check if the key matches the next key in the Konami code
        if (e.key === konamiCode[konamiIndex]) {
            // Create golden flash effect for correct input
            createGoldenFlash();

            konamiIndex++;

            // If the full code is entered
            if (konamiIndex === konamiCode.length) {
                activateEasterEgg();
                konamiIndex = 0;
            }
        } else {
            // Only shake if we've started the sequence but made a mistake
            if (konamiIndex > 0) {
                // Create shake effect for incorrect input
                createScreenShake();
            }

            // Reset the sequence
            konamiIndex = 0;
        }
    });
}

// Create golden flash effect
function createGoldenFlash() {
    const flash = document.createElement('div');
    flash.classList.add('golden-flash');
    document.body.appendChild(flash);

    // Remove the flash element after animation completes
    setTimeout(() => {
        flash.remove();
    }, 300);
}

// Create screen shake effect
function createScreenShake() {
    document.body.classList.add('shake');

    // Remove the shake class after animation completes
    setTimeout(() => {
        document.body.classList.remove('shake');
    }, 500);
}

// Activate Easter egg
function activateEasterEgg() {
    // Redirect to Easter egg page immediately
    window.location.href = '/arr';
}
