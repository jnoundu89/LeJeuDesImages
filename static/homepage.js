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

    // Initialize carousels
    initCarousels();
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
    const classicModeCards = document.querySelectorAll('.mode-container > .mode-grid:first-of-type .mode-card');
    const experimentalModeCards = document.querySelectorAll('.mode-container > .mode-grid:last-of-type .mode-card');
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
            }, 500); // 0.5 second delay to enjoy the fireworks
        });
    });

    // Add effects to all mode cards
    const allModeCards = document.querySelectorAll('.mode-card');
    allModeCards.forEach(card => {
        // Add hover effect class
        card.classList.add('card-hover');

        // Add shine effect
        card.classList.add('shine');
    });

    // Add 3D-flip animation effect to classic mode cards
    const classicCarouselCards = document.querySelectorAll('#classic-modes-track .mode-card');
    classicCarouselCards.forEach(card => {
        card.addEventListener('click', function(e) {
            // Don't trigger if clicking on the button (it has its own handler now)
            if (e.target.classList.contains('mode-button')) return;

            // Find the button in this card
            const button = this.querySelector('.mode-button');
            if (button) {
                // Ensure opacity is 1 before animation starts
                this.style.opacity = '1';

                // Add 3D flip animation
                this.classList.add('flip-3d');

                // Add glow effect
                this.classList.add('glow');

                // Remove the animations after they complete
                setTimeout(() => {
                    this.classList.remove('flip-3d');
                    this.classList.remove('glow');

                    // Ensure opacity remains 1 after animation ends
                    this.style.opacity = '1';
                }, 1000); // 1 second delay for animation
            }
        });
    });

    // Add jello animation effect to experimental mode cards
    const experimentalCarouselCards = document.querySelectorAll('#experimental-modes-track .mode-card');
    experimentalCarouselCards.forEach(card => {
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
    let particles = [];
    const colors = [
        'rgba(255, 215, 0, 0.7)',  // Gold
        'rgba(63, 81, 181, 0.5)',  // Primary
        'rgba(0, 150, 136, 0.5)',  // Secondary
        'rgba(255, 255, 255, 0.5)' // White
    ];

    // Function to create particles
    function createParticles() {
        particles = []; // Clear existing particles
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
    }

    // Create initial particles
    createParticles();

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
        // Recreate particles to distribute them across the new canvas size
        createParticles();
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

// Initialize carousels
function initCarousels() {
    // Initialize classic modes carousel
    initCarousel('classic-modes-track', 'classic-modes-indicators');

    // Initialize experimental modes carousel
    initCarousel('experimental-modes-track', 'experimental-modes-indicators');
}

// Initialize a single carousel
function initCarousel(trackId, indicatorsId) {
    const track = document.getElementById(trackId);
    if (!track) return;

    const wrapper = track.parentElement;
    const container = wrapper.parentElement.parentElement;
    const items = track.querySelectorAll('.carousel-item');
    const prevButton = container.querySelector('.prev-button');
    const nextButton = container.querySelector('.next-button');
    const indicatorsContainer = document.getElementById(indicatorsId);

    let currentIndex = 0;
    let startX, moveX;
    let isDragging = false;
    let itemsPerSlide = 1;

    // Function to determine how many items per slide based on screen width
    function updateItemsPerSlide() {
        if (window.innerWidth >= 1200) {
            itemsPerSlide = 3;
        } else if (window.innerWidth >= 768) {
            itemsPerSlide = 2;
        } else {
            itemsPerSlide = 1;
        }

        // Update the current slide position after resize
        goToSlide(Math.floor(currentIndex / itemsPerSlide) * itemsPerSlide);
    }

    // Create indicators based on number of slides (not items)
    function createIndicators() {
        // Clear existing indicators
        indicatorsContainer.innerHTML = '';

        // Calculate number of slides
        const slideCount = Math.ceil(items.length / itemsPerSlide);

        // Create new indicators
        for (let i = 0; i < slideCount; i++) {
            const indicator = document.createElement('div');
            indicator.classList.add('carousel-indicator');
            if (i === Math.floor(currentIndex / itemsPerSlide)) {
                indicator.classList.add('active');
            }
            indicator.addEventListener('click', () => goToSlide(i * itemsPerSlide));
            indicatorsContainer.appendChild(indicator);
        }
    }

    // Update indicators
    function updateIndicators() {
        const indicators = indicatorsContainer.querySelectorAll('.carousel-indicator');
        const currentSlide = Math.floor(currentIndex / itemsPerSlide);

        indicators.forEach((indicator, index) => {
            if (index === currentSlide) {
                indicator.classList.add('active');
            } else {
                indicator.classList.remove('active');
            }
        });
    }

    // Go to a specific slide
    function goToSlide(index) {
        // Ensure index is a multiple of itemsPerSlide, except for the last slide
        if (index % itemsPerSlide !== 0 && index + itemsPerSlide < items.length) {
            index = Math.floor(index / itemsPerSlide) * itemsPerSlide;
        }

        // Calculate max index that ensures we show the last items correctly
        const lastSlideIndex = Math.floor((items.length - 1) / itemsPerSlide) * itemsPerSlide;

        if (index < 0) index = lastSlideIndex;
        if (index > lastSlideIndex) index = 0;

        currentIndex = index;
        // Calculate the percentage to move based on the item width and number of items per slide
        const itemWidth = 100 / itemsPerSlide; // Width of each item as a percentage
        const translatePercentage = (currentIndex * itemWidth);
        track.style.transform = `translateX(-${translatePercentage}%)`;
        updateIndicators();
    }

    // Event listeners for buttons
    if (prevButton) {
        prevButton.addEventListener('click', () => {
            goToSlide(currentIndex - itemsPerSlide);
        });
    }

    if (nextButton) {
        nextButton.addEventListener('click', () => {
            goToSlide(currentIndex + itemsPerSlide);
        });
    }

    // Initialize responsive behavior
    updateItemsPerSlide();
    createIndicators();

    // Update on window resize
    window.addEventListener('resize', () => {
        updateItemsPerSlide();
        createIndicators();
    });

    // Touch events for swiping - only on navigation buttons and indicators
    // We're removing touch events from the track to prevent slide changes when touching cards

    // Add touch events to navigation buttons
    if (prevButton) {
        prevButton.addEventListener('touchstart', (e) => {
            e.stopPropagation(); // Prevent event from bubbling to track
        }, { passive: true });

        prevButton.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent event from bubbling to track
        });
    }

    if (nextButton) {
        nextButton.addEventListener('touchstart', (e) => {
            e.stopPropagation(); // Prevent event from bubbling to track
        }, { passive: true });

        nextButton.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent event from bubbling to track
        });
    }

    // Add touch events to indicators
    const indicators = indicatorsContainer.querySelectorAll('.carousel-indicator');
    indicators.forEach(indicator => {
        indicator.addEventListener('touchstart', (e) => {
            e.stopPropagation(); // Prevent event from bubbling to track
        }, { passive: true });

        indicator.addEventListener('click', (e) => {
            e.stopPropagation(); // Prevent event from bubbling to track
        });
    });

    // Mouse events for swiping (desktop)
    // Only allow swiping when initiated on the navigation buttons or indicators
    // We're removing the mousedown event on the track to prevent slide changes when clicking on cards

    // We still need mousemove and mouseup events for when dragging is initiated by touch events
    track.addEventListener('mousemove', (e) => {
        if (!isDragging) return;
        moveX = e.clientX;
    });

    track.addEventListener('mouseup', () => {
        if (!isDragging) return;
        isDragging = false;

        const diff = moveX - startX;
        if (diff > 50) {
            // Swipe right - go to previous slide
            goToSlide(currentIndex - itemsPerSlide);
        } else if (diff < -50) {
            // Swipe left - go to next slide
            goToSlide(currentIndex + itemsPerSlide);
        }
    });

    track.addEventListener('mouseleave', () => {
        if (isDragging) {
            isDragging = false;
        }
    });

    // Initialize the carousel
    goToSlide(0);
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
