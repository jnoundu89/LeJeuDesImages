// Enhanced animations for LeJeuDesImages
document.addEventListener('DOMContentLoaded', function() {
    // Add fade-in animation to main layout
    const mainLayout = document.querySelector('.main-layout');
    if (mainLayout) {
        mainLayout.classList.add('fade-in');
    }

    // Add staggered fade-in to stats items
    const statsBanner = document.getElementById('stats-banner');
    if (statsBanner) {
        const statsItems = statsBanner.querySelectorAll('p');
        statsItems.forEach((item, index) => {
            item.style.opacity = '0';
            item.style.animation = 'fadeIn 0.5s ease-out forwards';
            item.style.animationDelay = `${0.1 * (index + 1)}s`;
        });
    }

    // Add profile-image class to employee photos
    const employeeImages = document.querySelectorAll('img[alt="Photo d\'employé"]');
    employeeImages.forEach(img => {
        img.classList.add('profile-image');
    });

    // Wrap timer text in span for better styling
    const timerElement = document.getElementById('timer');
    if (timerElement && !timerElement.querySelector('span')) {
        const timerText = timerElement.textContent;
        timerElement.innerHTML = `<span>${timerText}</span>`;
    }

    // Add float animation to center content
    const centerContent = document.querySelector('.center-content');
    if (centerContent) {
        centerContent.classList.add('float');
    }

    // Add button classes to choice buttons
    const choiceButtons = document.querySelectorAll('.choice-btn');
    choiceButtons.forEach(btn => {
        if (!btn.classList.contains('normal-choice-btn')) {
            btn.classList.add('btn-primary');
        }
        // Add hover-fix class to prevent hover flickering
        btn.classList.add('hover-fix');
    });

    // Add accent class to toggle stats button
    const toggleStatsBtn = document.querySelector('.toggle-stats-btn');
    if (toggleStatsBtn) {
        toggleStatsBtn.classList.add('btn-accent', 'btn-small');
        // Add hover-fix class to prevent hover flickering
        toggleStatsBtn.classList.add('hover-fix');
    }

    // Add primary class to next button
    const nextButton = document.getElementById('next');
    if (nextButton) {
        nextButton.classList.add('btn-primary', 'btn-large');
        // Add hover-fix class to prevent hover flickering
        nextButton.classList.add('hover-fix');
    }

    // Add secondary class to restart button
    const restartButton = document.querySelector('.top-right');
    if (restartButton) {
        restartButton.classList.add('btn-secondary', 'btn-small');
        // Add hover-fix class to prevent hover flickering
        restartButton.classList.add('hover-fix');
    }

    // Add hover-fix class to all elements that have upward transformations on hover
    // This prevents the hover state from being lost when the element moves up
    const elementsWithHoverUp = document.querySelectorAll('.normal-choice-btn, .mode-card, .mode-button, button, .btn, .stats, #current-score, #high-score, .score');
    elementsWithHoverUp.forEach(element => {
        element.classList.add('hover-fix');
    });
});
