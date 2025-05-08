// homepage.js - Enhanced interactions for the homepage

document.addEventListener('DOMContentLoaded', function() {
    // Initialize animations
    initAnimations();

    // Initialize mode cards interaction
    initModeCards();

    // Initialize a particle background
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
    const modeButtons = document.querySelectorAll('.mode-button');

    // Add fireworks effect to all play buttons
    modeButtons.forEach(button => {
        button.addEventListener('click', function(e) {
            // Prevent default to stop immediate navigation
            e.preventDefault();

            // Store the href to navigate to later
            const href = this.getAttribute('href');

            // Create fireworks effect
            createFireworks();

            // Navigate after a delay to enjoy the fireworks
            setTimeout(() => {
                window.location.href = href;
            }, 500); // 1 second delay to enjoy the fireworks
        });
    });

    modeCards.forEach(card => {
        // Add hover effect class
        card.classList.add('card-hover');

        // Add shine effect
        card.classList.add('shine');

        // Add click effect
        card.addEventListener('click', function(e) {
            // Don't trigger if clicking on the button (it has its own handler now)
            if (e.target.classList.contains('mode-button')) return;

            // Find the button in this card
            const button = this.querySelector('.mode-button');
            if (button) {
                // Add jello animation
                this.classList.add('jello');

                // Remove the animation after it completes
                setTimeout(() => {
                    this.classList.remove('jello');
                }, 1000); // 1 second delay for animation
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
    // Create fireworks effect
    createFireworks();

    // Redirect to Easter egg page after fireworks display
    setTimeout(() => {
        window.location.href = '/arr';
    }, 3000); // 3 seconds delay to enjoy the fireworks
}

// Create fireworks effect
function createFireworks() {
    // Create container for fireworks
    const fireworksContainer = document.createElement('div');
    fireworksContainer.classList.add('fireworks-container');
    document.body.appendChild(fireworksContainer);

    // Create multiple fireworks with different colors, positions and timings
    const fireworksCount = 20;
    const colors = [
        'rgba(255, 0, 0, 0.8)',    // Red
        'rgba(0, 255, 0, 0.8)',    // Green
        'rgba(0, 0, 255, 0.8)',    // Blue
        'rgba(255, 255, 0, 0.8)',  // Yellow
        'rgba(255, 0, 255, 0.8)',  // Magenta
        'rgba(0, 255, 255, 0.8)',  // Cyan
        'rgba(255, 215, 0, 0.8)',  // Gold
        'rgba(255, 255, 255, 0.8)' // White
    ];

    for (let i = 0; i < fireworksCount; i++) {
        setTimeout(() => {
            launchFirework(fireworksContainer, colors);
        }, i * 150); // Stagger the fireworks
    }
}

// Launch a single firework
function launchFirework(container, colors) {
    // Create the firework element
    const firework = document.createElement('div');
    firework.classList.add('firework');

    // Random position, color, and animation properties
    const x = Math.random() * 100; // Random x position (0-100%)
    const color = colors[Math.floor(Math.random() * colors.length)];
    const duration = Math.random() * 0.5 + 0.5; // Random duration (0.5-1s)

    // Set custom properties for the animation
    firework.style.setProperty('--x', `${x}vw`);
    firework.style.setProperty('--color', color);
    firework.style.setProperty('--duration', `${duration}s`);

    // Create multiple particles from this firework
    const particleCount = 12;
    for (let i = 0; i < particleCount; i++) {
        const particle = document.createElement('div');
        particle.classList.add('firework');

        // Calculate angle for this particle (full circle divided by particleCount)
        const angle = (i / particleCount) * (2 * Math.PI);
        const distance = 20 + Math.random() * 30; // Random distance from center

        // Calculate end position based on angle and distance
        const xEnd = Math.cos(angle) * distance;
        const yEnd = Math.sin(angle) * distance;

        // Set custom properties for this particle
        particle.style.setProperty('--x', `${x}vw`);
        particle.style.setProperty('--xEnd', `${xEnd}vmin`);
        particle.style.setProperty('--yEnd', `${-yEnd}vmin`); // Negative to go upwards
        particle.style.setProperty('--color', color);
        particle.style.setProperty('--duration', `${duration}s`);

        // Add particle to container
        container.appendChild(particle);

        // Remove particle after animation completes
        setTimeout(() => {
            particle.remove();
        }, duration * 1000);
    }

    // Remove firework container after all animations complete
    setTimeout(() => {
        if (container.parentNode) {
            container.remove();
        }
    }, 3000);
}
