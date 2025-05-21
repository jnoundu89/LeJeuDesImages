// fireworks-responsive.js - Make fireworks canvas responsive for all resolutions

// Auto-inject this script into any page that has a fireworks container
(function() {
    // Create a new script element
    const script = document.createElement('script');
    script.type = 'text/javascript';
    script.textContent = `
        // Wait for the DOM to be fully loaded
        document.addEventListener('DOMContentLoaded', function() {
            // Check if the page has a fireworks container
            const fireworksContainer = document.getElementById('fireworks-container');
            if (!fireworksContainer) return;

            console.log('Fireworks container found, initializing responsive fireworks');

            // Add resize event listener to handle window resizing
            window.addEventListener('resize', handleResize);

            // Function to handle window resize
            function handleResize() {
                const canvas = document.getElementById('fireworks-canvas');
                if (canvas) {
                    // Update canvas dimensions
                    canvas.width = window.innerWidth;
                    canvas.height = window.innerHeight;

                    // If the fireworks are active, recreate them
                    if (window.fireworksActive) {
                        // Clear existing particles
                        window.fireworksParticles = [];

                        // Create new particles at the center of the screen
                        for (let i = 0; i < 100; i++) {
                            createFireworkParticle(canvas.width / 2, canvas.height / 2);
                        }
                    }
                }
            }

            // Function to create a firework particle (will be called from the original code)
            function createFireworkParticle(x, y) {
                if (!window.fireworksParticles || !window.fireworksColors) return;

                const color = window.fireworksColors[Math.floor(Math.random() * window.fireworksColors.length)];
                const particle = {
                    x: x,
                    y: y,
                    radius: Math.random() * 4 + 1,
                    color: color,
                    speed: Math.random() * 5 + 2,
                    angle: Math.random() * 2 * Math.PI,
                    alpha: 1,
                    decay: Math.random() * 0.03 + 0.01
                };
                window.fireworksParticles.push(particle);
            }

            // Override the showFireworks function to make it responsive
            const originalShowFireworks = window.showFireworks;
            window.showFireworks = function() {
                // Call the original function if it exists
                if (typeof originalShowFireworks === 'function') {
                    originalShowFireworks();
                } else {
                    // If the original function doesn't exist, implement our own
                    const fireworksContainer = document.getElementById('fireworks-container');
                    if (!fireworksContainer) return;

                    fireworksContainer.innerHTML = '<canvas id="fireworks-canvas"></canvas>';
                    const canvas = document.getElementById('fireworks-canvas');
                    const ctx = canvas.getContext('2d');
                    canvas.width = window.innerWidth;
                    canvas.height = window.innerHeight;

                    // Store particles and colors in global variables for access during resize
                    window.fireworksParticles = [];
                    window.fireworksColors = ['#FF1461', '#18FF92', '#5A87FF', '#FBF38C'];
                    window.fireworksActive = true;

                    // Create initial particles
                    for (let i = 0; i < 100; i++) {
                        createFireworkParticle(canvas.width / 2, canvas.height / 2);
                    }

                    // Animation loop
                    function loop() {
                        if (!window.fireworksActive) return;

                        // Update particles
                        for (let i = window.fireworksParticles.length - 1; i >= 0; i--) {
                            const p = window.fireworksParticles[i];
                            p.x += p.speed * Math.cos(p.angle);
                            p.y += p.speed * Math.sin(p.angle);
                            p.alpha -= p.decay;
                            if (p.alpha <= 0) {
                                window.fireworksParticles.splice(i, 1);
                            }
                        }

                        // Draw particles
                        ctx.clearRect(0, 0, canvas.width, canvas.height);
                        window.fireworksParticles.forEach(p => {
                            ctx.globalAlpha = p.alpha;
                            ctx.beginPath();
                            ctx.arc(p.x, p.y, p.radius, 0, 2 * Math.PI);
                            ctx.fillStyle = p.color;
                            ctx.fill();
                        });

                        requestAnimationFrame(loop);
                    }

                    loop();
                }
            };
        });
    `;

    // Append the script to the head
    document.head.appendChild(script);
})();
