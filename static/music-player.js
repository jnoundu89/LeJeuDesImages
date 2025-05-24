// music-player.js - Background music and audio visualization for the homepage

// Audio context and analyzer for visualizations
let audioContext;
let analyzer;
let dataArray;
let bufferLength;

// Music state
let isMusicPlaying = false;
let isMusicMuted = false;
let currentVolume = 0.7; // Default volume
let musicVisualizerActive = true;
let currentTrackIndex = 0;

// Music tracks - array of objects with title and path
const musicTracks = [
    {
        title: "Cosmic Adventure",
        path: "https://cdn.pixabay.com/download/audio/2022/03/15/audio_c8e9124b46.mp3?filename=electronic-future-beats-117997.mp3",
        artist: "Alex Productions",
        color: "rgba(63, 81, 181, 0.8)"
    },
    {
        title: "Digital Dreams",
        path: "https://cdn.pixabay.com/download/audio/2022/01/18/audio_d0c6ff1bcc.mp3?filename=digital-dreamscape-118515.mp3",
        artist: "Music Unlimited",
        color: "rgba(0, 150, 136, 0.8)"
    },
    {
        title: "Neon Lights",
        path: "https://cdn.pixabay.com/download/audio/2022/10/25/audio_946bc1fcc0.mp3?filename=electronic-rock-king-around-here-15045.mp3",
        artist: "Lexin Music",
        color: "rgba(255, 87, 34, 0.8)"
    }
];

// Initialize music player when document is loaded
document.addEventListener('DOMContentLoaded', function() {
    initMusicPlayer();
});

// Initialize the music player
function initMusicPlayer() {
    // Create audio element if it doesn't exist
    let audioElement = document.getElementById('background-music');
    if (!audioElement) {
        audioElement = document.createElement('audio');
        audioElement.id = 'background-music';
        audioElement.loop = false; // We'll handle looping manually to switch tracks
        audioElement.volume = currentVolume;
        document.body.appendChild(audioElement);
    }

    // Set initial track
    setCurrentTrack(currentTrackIndex);

    // Add event listeners
    audioElement.addEventListener('ended', function() {
        // Play next track when current one ends
        currentTrackIndex = (currentTrackIndex + 1) % musicTracks.length;
        setCurrentTrack(currentTrackIndex);
        if (isMusicPlaying) {
            audioElement.play();
        }
        updateTrackInfo();
    });

    // Initialize audio context for visualizations
    try {
        audioContext = new (window.AudioContext || window.webkitAudioContext)();

        // Create analyzer
        analyzer = audioContext.createAnalyser();
        analyzer.fftSize = 256;
        bufferLength = analyzer.frequencyBinCount;
        dataArray = new Uint8Array(bufferLength);

        // Create media element source
        const source = audioContext.createMediaElementSource(audioElement);
        source.connect(analyzer);
        analyzer.connect(audioContext.destination);

        // Start visualization loop
        visualize();
    } catch (e) {
        console.error('Web Audio API is not supported in this browser', e);
        // Disable visualizer if Web Audio API is not supported
        musicVisualizerActive = false;
    }

    // Set up music controls
    setupMusicControls();

    // Update track info display
    updateTrackInfo();
}

// Set up music control buttons
function setupMusicControls() {
    // Play/Pause button
    const playPauseBtn = document.getElementById('music-play-pause');
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', togglePlayPause);
    }

    // Mute button
    const muteBtn = document.getElementById('music-mute');
    if (muteBtn) {
        muteBtn.addEventListener('click', toggleMute);
    }

    // Next track button
    const nextBtn = document.getElementById('music-next');
    if (nextBtn) {
        nextBtn.addEventListener('click', playNextTrack);
    }

    // Previous track button
    const prevBtn = document.getElementById('music-prev');
    if (prevBtn) {
        prevBtn.addEventListener('click', playPrevTrack);
    }

    // Volume slider
    const volumeSlider = document.getElementById('music-volume');
    if (volumeSlider) {
        volumeSlider.value = currentVolume * 100;
        volumeSlider.addEventListener('input', function() {
            setVolume(this.value / 100);
        });
    }

    // Visualizer toggle
    const visualizerToggle = document.getElementById('visualizer-toggle');
    if (visualizerToggle) {
        visualizerToggle.addEventListener('click', toggleVisualizer);
    }
}

// Toggle play/pause
function togglePlayPause() {
    const audioElement = document.getElementById('background-music');
    const playPauseBtn = document.getElementById('music-play-pause');

    if (!audioElement) return;

    if (audioContext && audioContext.state === 'suspended') {
        audioContext.resume();
    }

    if (isMusicPlaying) {
        audioElement.pause();
        isMusicPlaying = false;
        if (playPauseBtn) {
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
            playPauseBtn.title = 'Jouer la musique';
        }
    } else {
        audioElement.play().catch(e => {
            console.error('Error playing audio:', e);
            // Show a message to the user about interaction being required
            showPlaybackMessage();
        });
        isMusicPlaying = true;
        if (playPauseBtn) {
            playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
            playPauseBtn.title = 'Mettre en pause';
        }

        // Start audio spectrum effect
        startAudioSpectrumEffect();
    }

    // Update music player UI
    updateMusicPlayerUI();
}

// Toggle mute
function toggleMute() {
    const audioElement = document.getElementById('background-music');
    const muteBtn = document.getElementById('music-mute');

    if (!audioElement) return;

    if (isMusicMuted) {
        audioElement.volume = currentVolume;
        isMusicMuted = false;
        if (muteBtn) {
            muteBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
            muteBtn.title = 'Couper le son';
        }
    } else {
        audioElement.volume = 0;
        isMusicMuted = true;
        if (muteBtn) {
            muteBtn.innerHTML = '<i class="fas fa-volume-mute"></i>';
            muteBtn.title = 'Activer le son';
        }
    }
}

// Set volume
function setVolume(value) {
    const audioElement = document.getElementById('background-music');
    if (!audioElement) return;

    currentVolume = value;
    if (!isMusicMuted) {
        audioElement.volume = currentVolume;
    }

    // Update volume icon based on level
    updateVolumeIcon();
}

// Update volume icon based on current volume
function updateVolumeIcon() {
    const muteBtn = document.getElementById('music-mute');
    if (!muteBtn) return;

    if (isMusicMuted) {
        muteBtn.innerHTML = '<i class="fas fa-volume-mute"></i>';
    } else if (currentVolume === 0) {
        muteBtn.innerHTML = '<i class="fas fa-volume-off"></i>';
    } else if (currentVolume < 0.5) {
        muteBtn.innerHTML = '<i class="fas fa-volume-down"></i>';
    } else {
        muteBtn.innerHTML = '<i class="fas fa-volume-up"></i>';
    }
}

// Play next track
function playNextTrack() {
    currentTrackIndex = (currentTrackIndex + 1) % musicTracks.length;
    setCurrentTrack(currentTrackIndex);

    const audioElement = document.getElementById('background-music');
    if (audioElement && isMusicPlaying) {
        audioElement.play().catch(e => console.error('Error playing next track:', e));
    }

    // Update track info display
    updateTrackInfo();

    // Add track change animation
    animateTrackChange();
}

// Play previous track
function playPrevTrack() {
    currentTrackIndex = (currentTrackIndex - 1 + musicTracks.length) % musicTracks.length;
    setCurrentTrack(currentTrackIndex);

    const audioElement = document.getElementById('background-music');
    if (audioElement && isMusicPlaying) {
        audioElement.play().catch(e => console.error('Error playing previous track:', e));
    }

    // Update track info display
    updateTrackInfo();

    // Add track change animation
    animateTrackChange();
}

// Set current track
function setCurrentTrack(index) {
    const audioElement = document.getElementById('background-music');
    if (!audioElement) return;

    audioElement.src = musicTracks[index].path;
    audioElement.load();
}

// Update track info display
function updateTrackInfo() {
    const trackTitle = document.getElementById('track-title');
    const trackArtist = document.getElementById('track-artist');

    if (trackTitle) {
        trackTitle.textContent = musicTracks[currentTrackIndex].title;
    }

    if (trackArtist) {
        trackArtist.textContent = musicTracks[currentTrackIndex].artist;
    }

    // Update music player color theme based on track
    updateMusicPlayerTheme();
}

// Update music player theme based on current track
function updateMusicPlayerTheme() {
    const musicPlayer = document.getElementById('music-player');
    if (!musicPlayer) return;

    // Set color theme based on current track
    const trackColor = musicTracks[currentTrackIndex].color;
    musicPlayer.style.setProperty('--music-player-accent', trackColor);

    // Add color transition effect
    musicPlayer.classList.add('color-transition');
    setTimeout(() => {
        musicPlayer.classList.remove('color-transition');
    }, 1000);
}

// Toggle visualizer
function toggleVisualizer() {
    const visualizerToggle = document.getElementById('visualizer-toggle');
    const visualizer = document.getElementById('music-visualizer');

    musicVisualizerActive = !musicVisualizerActive;

    if (visualizerToggle) {
        if (musicVisualizerActive) {
            visualizerToggle.innerHTML = '<i class="fas fa-eye"></i>';
            visualizerToggle.title = 'Masquer le visualiseur';
        } else {
            visualizerToggle.innerHTML = '<i class="fas fa-eye-slash"></i>';
            visualizerToggle.title = 'Afficher le visualiseur';
        }
    }

    if (visualizer) {
        if (musicVisualizerActive) {
            visualizer.classList.remove('hidden');
        } else {
            visualizer.classList.add('hidden');
        }
    }
}

// Visualize the music
function visualize() {
    const visualizer = document.getElementById('music-visualizer');
    if (!visualizer || !analyzer || !musicVisualizerActive) {
        requestAnimationFrame(visualize);
        return;
    }

    // Get frequency data
    analyzer.getByteFrequencyData(dataArray);

    // Clear the canvas
    const canvas = visualizer;
    const ctx = canvas.getContext('2d');
    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Set canvas dimensions to match container
    const container = visualizer.parentElement;
    if (container) {
        canvas.width = container.clientWidth;
        canvas.height = container.clientHeight;
    }

    // Draw visualization
    const barWidth = (canvas.width / bufferLength) * 2.5;
    let x = 0;

    for (let i = 0; i < bufferLength; i++) {
        const barHeight = (dataArray[i] / 255) * canvas.height * 0.8;

        // Use current track color for visualization
        const trackColor = musicTracks[currentTrackIndex].color;
        const r = parseInt(trackColor.substring(5, trackColor.indexOf(',')), 10);
        const g = parseInt(trackColor.substring(trackColor.indexOf(',') + 1, trackColor.lastIndexOf(',')), 10);
        const b = parseInt(trackColor.substring(trackColor.lastIndexOf(',') + 1, trackColor.lastIndexOf(')')), 10);

        // Create gradient based on frequency
        const gradient = ctx.createLinearGradient(0, canvas.height - barHeight, 0, canvas.height);
        gradient.addColorStop(0, `rgba(${r}, ${g}, ${b}, 0.8)`);
        gradient.addColorStop(1, `rgba(${r}, ${g}, ${b}, 0.2)`);

        ctx.fillStyle = gradient;
        ctx.fillRect(x, canvas.height - barHeight, barWidth, barHeight);

        x += barWidth + 1;
    }

    // Continue animation loop
    requestAnimationFrame(visualize);
}

// Show message about playback requiring user interaction
function showPlaybackMessage() {
    const messageContainer = document.createElement('div');
    messageContainer.className = 'playback-message';
    messageContainer.innerHTML = `
        <div class="playback-message-content">
            <i class="fas fa-music"></i>
            <p>Cliquez pour activer la musique</p>
        </div>
    `;

    document.body.appendChild(messageContainer);

    // Add click event to start playback
    messageContainer.addEventListener('click', function() {
        const audioElement = document.getElementById('background-music');
        if (audioElement) {
            audioElement.play().then(() => {
                isMusicPlaying = true;
                updateMusicPlayerUI();
                messageContainer.remove();
            }).catch(e => console.error('Error starting playback:', e));
        }
    });

    // Auto-remove after 5 seconds
    setTimeout(() => {
        if (document.body.contains(messageContainer)) {
            messageContainer.remove();
        }
    }, 5000);
}

// Update music player UI based on current state
function updateMusicPlayerUI() {
    const playPauseBtn = document.getElementById('music-play-pause');
    const musicPlayer = document.getElementById('music-player');

    if (playPauseBtn) {
        if (isMusicPlaying) {
            playPauseBtn.innerHTML = '<i class="fas fa-pause"></i>';
            playPauseBtn.title = 'Mettre en pause';
        } else {
            playPauseBtn.innerHTML = '<i class="fas fa-play"></i>';
            playPauseBtn.title = 'Jouer la musique';
        }
    }

    if (musicPlayer) {
        if (isMusicPlaying) {
            musicPlayer.classList.add('playing');
        } else {
            musicPlayer.classList.remove('playing');
        }
    }

    // Update music player container class
    const musicPlayerContainer = document.querySelector('.music-player-container');
    if (musicPlayerContainer) {
        if (isMusicPlaying) {
            musicPlayerContainer.classList.add('playing');
        } else {
            musicPlayerContainer.classList.remove('playing');
        }
    }

    // Update volume icon
    updateVolumeIcon();
}

// Animate track change with a pulse effect
function animateTrackChange() {
    const musicPlayer = document.getElementById('music-player');
    if (!musicPlayer) return;

    musicPlayer.classList.add('track-change-pulse');
    setTimeout(() => {
        musicPlayer.classList.remove('track-change-pulse');
    }, 500);
}

// Create audio spectrum analyzer effect that reacts to the music
function createAudioSpectrumEffect() {
    if (!analyzer || !musicVisualizerActive) return;

    // Get frequency data
    analyzer.getByteFrequencyData(dataArray);

    // Calculate average frequency value
    let sum = 0;
    for (let i = 0; i < bufferLength; i++) {
        sum += dataArray[i];
    }
    const average = sum / bufferLength;

    // Use average to affect page elements
    const intensity = average / 255;

    // Apply pulse effect to logo based on beat
    const logo = document.querySelector('.game-logo');
    if (logo) {
        logo.style.transform = `scale(${1 + intensity * 0.05})`;
    }

    // Apply subtle glow to header based on music intensity
    const header = document.querySelector('.game-header');
    if (header) {
        header.style.boxShadow = `0 0 ${20 * intensity}px rgba(255, 215, 0, ${0.3 + intensity * 0.3})`;
    }

    // Continue the effect loop
    requestAnimationFrame(createAudioSpectrumEffect);
}

// Start audio spectrum effect when music is playing
function startAudioSpectrumEffect() {
    if (isMusicPlaying && musicVisualizerActive) {
        createAudioSpectrumEffect();
    }
}

// Start the audio spectrum effect when music starts playing
document.addEventListener('DOMContentLoaded', function() {
    const musicPlayerContainer = document.querySelector('.music-player-container');

    // Add click event to the music toggle button to show the music player
    const toggleMusicBtn = document.getElementById('toggle-music-btn');
    if (toggleMusicBtn && musicPlayerContainer) {
        toggleMusicBtn.addEventListener('click', function() {
            musicPlayerContainer.classList.add('expanded');
        });
    }

    // Add click event to the minimize button to hide the music player
    const minimizeBtn = document.getElementById('minimize-player-btn');
    if (minimizeBtn && musicPlayerContainer) {
        minimizeBtn.addEventListener('click', function() {
            musicPlayerContainer.classList.remove('expanded');
        });
    }

    // Start audio spectrum effect when play button is clicked
    const playPauseBtn = document.getElementById('music-play-pause');
    if (playPauseBtn) {
        playPauseBtn.addEventListener('click', function() {
            if (isMusicPlaying) {
                startAudioSpectrumEffect();
            }
        });
    }
});
