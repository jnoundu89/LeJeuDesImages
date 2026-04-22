// bouncing-images.js - Implements the bouncing image animation

// Global variable to track if animation is enabled
let isAnimationEnabled = false;

document.addEventListener('DOMContentLoaded', function() {
    // Initialize the bouncing image animation
    initBouncingImage();
});

// Array to store employee image URLs
let employeeImages = [];

// Array of colors for the halo effect
let haloColors = [
    'rgba(255, 215, 0, 0.7)',    // Gold (original)
    'rgba(255, 0, 0, 0.7)',      // Red
    'rgba(0, 255, 0, 0.7)',      // Green
    'rgba(0, 0, 255, 0.7)',      // Blue
    'rgba(255, 0, 255, 0.7)',    // Magenta
    'rgba(0, 255, 255, 0.7)',    // Cyan
    'rgba(255, 165, 0, 0.7)',    // Orange
    'rgba(128, 0, 128, 0.7)',    // Purple
    'rgba(0, 128, 0, 0.7)',      // Dark Green
    'rgba(255, 192, 203, 0.7)'   // Pink
];
let currentColorIndex = 0;

// Current position and velocity
let posX = 0;
let posY = 0;
let velX = 1.5;
let velY = 1.5;
let isPaused = false;

// Container dimensions
let containerWidth = 120;
let containerHeight = 120;

// Window dimensions
let windowWidth = window.innerWidth;
let windowHeight = window.innerHeight;

// Current image index
let currentImageIndex = 0;
let nextImageIndex = 1;

// Initialize the bouncing image animation
function initBouncingImage() {
    // Fetch employee data to get image URLs
    fetchEmployeeImages()
        .then(() => {
            // Create the bouncing image container
            createBouncingImageContainer();

            // Set initial state based on isAnimationEnabled
            const container = document.getElementById('bouncing-image-container');
            if (container && !isAnimationEnabled) {
                container.style.display = 'none';

                // Update button icon/text
                const toggleBtn = document.getElementById('toggle-animation-btn');
                if (toggleBtn) {
                    toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
                    toggleBtn.title = 'Afficher l\'animation';
                }
            }

            // Start the animation loop
            requestAnimationFrame(animateBouncingImage);

            // Start image transition timer
            setInterval(transitionToNextImage, 5000);
        })
        .catch(error => console.error('Error initializing bouncing image:', error));

    // Handle window resize
    window.addEventListener('resize', function() {
        windowWidth = window.innerWidth;
        windowHeight = window.innerHeight;
    });
}

// Fetch employee images from the API
async function fetchEmployeeImages() {
    try {
        // Fetch all employee image URLs from the API
        const response = await fetch('/api/employee_images');

        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }

        // Parse the JSON response
        const imageUrls = await response.json();

        // If we couldn't get any image URLs, use a fallback array
        if (!imageUrls || imageUrls.length === 0) {
            console.warn('No image URLs found from API, using fallback array');
            employeeImages = [];
        } else {
            employeeImages = imageUrls;
        }

        // Shuffle the array to randomize the order
        shuffleArray(employeeImages);
        console.log(`Loaded ${employeeImages.length} employee images`);
    } catch (error) {
        console.error('Error fetching employee images:', error);
        // Use fallback array in case of error
        employeeImages = [];
        shuffleArray(employeeImages);
    }
}

// Create the bouncing image container
function createBouncingImageContainer() {
    // Create container
    const container = document.createElement('div');
    container.className = 'bouncing-image-container';
    container.id = 'bouncing-image-container';

    // Set initial position
    posX = Math.random() * (windowWidth - containerWidth);
    posY = Math.random() * (windowHeight - containerHeight);
    container.style.left = posX + 'px';
    container.style.top = posY + 'px';

    // Set initial halo color
    const initialColor = haloColors[currentColorIndex];
    container.style.boxShadow = `0 0 15px ${initialColor}`;

    // Set initial hover color
    const initialHoverColor = initialColor.replace('0.7', '1');
    container.dataset.hoverColor = initialHoverColor;
    updateHoverStyle(initialHoverColor);

    // Create two image elements for smooth transition
    const img1 = document.createElement('img');
    img1.className = 'bouncing-image fade-in';
    img1.id = 'bouncing-image-1';
    img1.src = employeeImages[0];
    img1.alt = 'Employee Image';

    const img2 = document.createElement('img');
    img2.className = 'bouncing-image fade-out';
    img2.id = 'bouncing-image-2';
    img2.src = employeeImages[1];
    img2.alt = 'Employee Image';
    img2.style.position = 'absolute';
    img2.style.top = '0';
    img2.style.left = '0';

    // Add images to container
    container.appendChild(img1);
    container.appendChild(img2);

    // Add event listeners for hover
    container.addEventListener('mouseenter', function() {
        isPaused = true;
    });

    container.addEventListener('mouseleave', function() {
        isPaused = false;
    });

    // Add click event to manually trigger image transition
    container.addEventListener('click', function() {
        transitionToNextImage();
    });

    // Add container to body
    document.body.appendChild(container);
}

// Animate the bouncing image
function animateBouncingImage() {
    const container = document.getElementById('bouncing-image-container');

    if (!container) {
        requestAnimationFrame(animateBouncingImage);
        return;
    }

    // Only update position if not paused
    if (!isPaused) {
        // Update position
        posX += velX;
        posY += velY;

        // Check for collisions with window edges
        if (posX <= 0 || posX >= windowWidth - containerWidth) {
            velX = -velX;
            // Ensure we don't get stuck at the edge
            posX = Math.max(0, Math.min(posX, windowWidth - containerWidth));
        }

        if (posY <= 0 || posY >= windowHeight - containerHeight) {
            velY = -velY;
            // Ensure we don't get stuck at the edge
            posY = Math.max(0, Math.min(posY, windowHeight - containerHeight));
        }

        // Update container position
        container.style.left = posX + 'px';
        container.style.top = posY + 'px';
    }

    // Continue animation loop
    requestAnimationFrame(animateBouncingImage);
}

// Transition to the next image with fade effect
function transitionToNextImage() {
    const img1 = document.getElementById('bouncing-image-1');
    const img2 = document.getElementById('bouncing-image-2');
    const container = document.getElementById('bouncing-image-container');

    if (!img1 || !img2 || !container) return;

    // Determine which image is currently visible
    const isImg1Visible = img1.classList.contains('fade-in');

    // Get next image index
    nextImageIndex = (currentImageIndex + 1) % employeeImages.length;

    // Update the hidden image with the next image
    if (isImg1Visible) {
        img2.src = employeeImages[nextImageIndex];
        img2.classList.remove('fade-out');
        img2.classList.add('fade-in');
        img1.classList.remove('fade-in');
        img1.classList.add('fade-out');
    } else {
        img1.src = employeeImages[nextImageIndex];
        img1.classList.remove('fade-out');
        img1.classList.add('fade-in');
        img2.classList.remove('fade-in');
        img2.classList.add('fade-out');
    }

    // Update current image index
    currentImageIndex = nextImageIndex;

    // Change the halo color
    currentColorIndex = (currentColorIndex + 1) % haloColors.length;
    const newColor = haloColors[currentColorIndex];

    // Apply the new color to the box-shadow
    container.style.boxShadow = `0 0 15px ${newColor}`;

    // Update the hover color by setting a custom property that can be used in CSS
    const hoverColor = newColor.replace('0.7', '1');
    container.dataset.hoverColor = hoverColor;

    // Add or update the hover style
    updateHoverStyle(hoverColor);
}

// Function to update the hover style for the bouncing image container
function updateHoverStyle(hoverColor) {
    // Check if our style element already exists
    let styleElement = document.getElementById('bouncing-image-hover-style');

    // If not, create it
    if (!styleElement) {
        styleElement = document.createElement('style');
        styleElement.id = 'bouncing-image-hover-style';
        document.head.appendChild(styleElement);
    }

    // Update the style content
    styleElement.textContent = `
        .bouncing-image-container:hover {
            box-shadow: 0 0 20px ${hoverColor} !important;
        }
    `;
}

// Toggle the bouncing image animation
function toggleBouncingAnimation() {
    const container = document.getElementById('bouncing-image-container');
    if (!container) return;

    isAnimationEnabled = !isAnimationEnabled;

    if (isAnimationEnabled) {
        container.style.display = 'block';
        // Update button icon/text if needed
        const toggleBtn = document.getElementById('toggle-animation-btn');
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="fas fa-eye-slash"></i>';
            toggleBtn.title = 'Masquer l\'animation';
        }
    } else {
        container.style.display = 'none';
        // Update button icon/text if needed
        const toggleBtn = document.getElementById('toggle-animation-btn');
        if (toggleBtn) {
            toggleBtn.innerHTML = '<i class="fas fa-eye"></i>';
            toggleBtn.title = 'Afficher l\'animation';
        }
    }
}

// Utility function to shuffle an array
function shuffleArray(array) {
    for (let i = array.length - 1; i > 0; i--) {
        const j = Math.floor(Math.random() * (i + 1));
        [array[i], array[j]] = [array[j], array[i]];
    }
    return array;
}
