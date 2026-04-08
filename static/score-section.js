/**
 * Enhanced Score Section Animations for LeJeuDesImages
 * This file contains animations and functionality for the score section across all game modes
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize score section animations
    initScoreSection();
    
    // Add event listeners for score updates
    addScoreUpdateListeners();
});

/**
 * Initialize the score section with animations and effects
 */
function initScoreSection() {
    // Get all score sections
    const scoreSections = document.querySelectorAll('.score-section');
    
    scoreSections.forEach(section => {
        // Add appear animation class
        section.classList.add('score-section-appear');
        
        // Add staggered animation to score items
        const scoreItems = section.querySelectorAll('p');
        scoreItems.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.animation = 'fadeIn 0.5s ease-out forwards';
            item.style.animationDelay = `${0.2 + (index * 0.1)}s`;
        });
        
        // Add special effects to score values
        const scoreValues = section.querySelectorAll('.score');
        scoreValues.forEach(value => {
            // Add data attribute to store original value for animation
            value.setAttribute('data-value', value.textContent);
            
            // Add hover effect
            value.addEventListener('mouseenter', function() {
                this.classList.add('score-hover');
            });
            
            value.addEventListener('mouseleave', function() {
                this.classList.remove('score-hover');
            });
        });
    });
}

/**
 * Add event listeners for score updates
 */
function addScoreUpdateListeners() {
    // Override the original checkAnswer function to add enhanced animations
    if (window.originalCheckAnswer === undefined && window.checkAnswer !== undefined) {
        window.originalCheckAnswer = window.checkAnswer;
        
        window.checkAnswer = function(correct, selected, element, currentScoreId, titleId) {
            // Call the original function
            window.originalCheckAnswer(correct, selected, element, currentScoreId, titleId);
            
            // Add enhanced animations for score updates
            const scoreElement = document.getElementById('current-score');
            if (scoreElement) {
                // Add particle effects for correct answers
                if (correct === selected) {
                    createScoreParticles(scoreElement);
                }
            }
        };
    }
    
    // Override the original checkImage function to add enhanced animations
    if (window.originalCheckImage === undefined && window.checkImage !== undefined) {
        window.originalCheckImage = window.checkImage;
        
        window.checkImage = function(correct, selected, element) {
            // Call the original function
            window.originalCheckImage(correct, selected, element);
            
            // Add enhanced animations for score updates
            const scoreElement = document.getElementById('current-score');
            if (scoreElement && correct === selected) {
                createScoreParticles(scoreElement);
            }
        };
    }
}

/**
 * Create particle effects for score updates
 * @param {HTMLElement} element - The element to create particles around
 */
function createScoreParticles(element) {
    // Get element position
    const rect = element.getBoundingClientRect();
    const centerX = rect.left + rect.width / 2;
    const centerY = rect.top + rect.height / 2;
    
    // Create particle container
    const particleContainer = document.createElement('div');
    particleContainer.className = 'score-particles';
    particleContainer.style.position = 'fixed';
    particleContainer.style.top = '0';
    particleContainer.style.left = '0';
    particleContainer.style.width = '100%';
    particleContainer.style.height = '100%';
    particleContainer.style.pointerEvents = 'none';
    particleContainer.style.zIndex = '9999';
    document.body.appendChild(particleContainer);
    
    // Create particles
    const colors = ['#FFD700', '#FFC107', '#FFEB3B', '#4CAF50'];
    
    for (let i = 0; i < 20; i++) {
        const particle = document.createElement('div');
        particle.className = 'score-particle';
        particle.style.position = 'absolute';
        particle.style.width = `${Math.random() * 10 + 5}px`;
        particle.style.height = particle.style.width;
        particle.style.backgroundColor = colors[Math.floor(Math.random() * colors.length)];
        particle.style.borderRadius = '50%';
        particle.style.top = `${centerY}px`;
        particle.style.left = `${centerX}px`;
        particle.style.transform = 'translate(-50%, -50%)';
        particle.style.opacity = '1';
        particle.style.transition = 'all 1s cubic-bezier(0.165, 0.84, 0.44, 1)';
        
        particleContainer.appendChild(particle);
        
        // Animate particles
        setTimeout(() => {
            const angle = Math.random() * Math.PI * 2;
            const distance = 50 + Math.random() * 100;
            particle.style.top = `${centerY + Math.sin(angle) * distance}px`;
            particle.style.left = `${centerX + Math.cos(angle) * distance}px`;
            particle.style.opacity = '0';
            particle.style.transform = `translate(-50%, -50%) scale(${Math.random() * 0.5 + 0.5})`;
        }, 10);
        
        // Remove particles after animation
        setTimeout(() => {
            if (particleContainer.contains(particle)) {
                particleContainer.removeChild(particle);
            }
            
            // Remove container if empty
            if (particleContainer.childElementCount === 0) {
                document.body.removeChild(particleContainer);
            }
        }, 1000);
    }
    
    // Add number increment animation to score value
    const scoreValueElement = element.querySelector('.score');
    if (scoreValueElement) {
        const currentValue = parseInt(scoreValueElement.textContent.split('/')[0]) || 0;
        const maxValue = parseInt(scoreValueElement.textContent.split('/')[1]) || 0;
        
        // Store original text
        const originalText = scoreValueElement.textContent;
        
        // Animate number increment
        animateNumberIncrement(scoreValueElement, currentValue - 1, currentValue, maxValue);
    }
}

/**
 * Animate number increment for score values
 * @param {HTMLElement} element - The element containing the score
 * @param {number} start - The starting value
 * @param {number} end - The ending value
 * @param {number} max - The maximum value
 */
function animateNumberIncrement(element, start, end, max) {
    const duration = 500; // ms
    const frameDuration = 1000 / 60; // 60fps
    const totalFrames = Math.round(duration / frameDuration);
    let frame = 0;
    
    // Start animation
    const animate = () => {
        frame++;
        const progress = frame / totalFrames;
        const currentValue = Math.floor(start + (end - start) * progress);
        
        // Update text
        element.textContent = `${currentValue}/${max}`;
        
        // Continue animation if not complete
        if (frame < totalFrames) {
            requestAnimationFrame(animate);
        }
    };
    
    // Start animation
    requestAnimationFrame(animate);
}