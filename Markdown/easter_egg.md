
# Easter Egg ARR Game Mode Implementation

Based on my analysis of the code, I'll implement a hidden ARR (Annual Recurring Revenue) game mode as an easter egg on the homepage. This game will challenge players to reach +15% ARR to earn employee bonuses.

## Current Implementation Status

I found that most of the components for this easter egg already exist:

1. **ARRMode Class**: A fully implemented game mode where players make strategic decisions to increase ARR by 15% over 12 months.
2. **Templates**: Both `arr.html` (introduction page) and `arr_mode.html` (actual game interface) exist.
3. **Konami Code**: There's already a Konami code easter egg in `scripts.js` that redirects to `/arr` when the sequence is entered.
4. **Route**: There's an `/arr` route in `game_routes.py` that renders the introduction page.

## Implementation Plan

The implementation is nearly complete, but needs a few adjustments to ensure everything works properly:

### 1. Update the ARR Easter Egg Route

The current `/arr` route in `game_routes.py` needs to be updated to properly explain the game and provide a way to start it. The route is already set up, but we need to make sure it's properly connected to the ARR mode.

```python
@game_bp.route('/arr')
def arr_easter_egg():
    """
    Easter egg route for the ARR game mode.
    """
    return render_template('arr.html')
```

This route is correctly rendering the introduction page (`arr.html`), which already has a button to start the ARR game mode.

### 2. Verify the Konami Code Implementation

The Konami code easter egg is already implemented in `scripts.js`:

```javascript
// Easter egg - Konami code (up, up, down, down, left, right, left, right, b, a)
let konamiCode = ['ArrowUp', 'ArrowUp', 'ArrowDown', 'ArrowDown', 'ArrowLeft', 'ArrowRight', 'ArrowLeft', 'ArrowRight', 'KeyB', 'KeyA'];
let konamiIndex = 0;

document.addEventListener('keydown', function(e) {
    // Check if the key pressed matches the next key in the Konami code
    if (e.code === konamiCode[konamiIndex]) {
        konamiIndex++;

        // If the entire code has been entered correctly
        if (konamiIndex === konamiCode.length) {
            // Reset the index
            konamiIndex = 0;

            // Redirect to the ARR game mode
            window.location.href = '/arr';
        }
    } else {
        // Reset the index if an incorrect key is pressed
        konamiIndex = 0;
    }
});
```

This code correctly listens for the Konami code sequence and redirects to the `/arr` route when it's entered.

### 3. Add Visual Feedback for Konami Code

To enhance the user experience, I'll add visual feedback when the Konami code is being entered. This will help users know they're on the right track.

```javascript
// Add to scripts.js
function flashScreen() {
    const overlay = document.createElement('div');
    overlay.style.position = 'fixed';
    overlay.style.top = '0';
    overlay.style.left = '0';
    overlay.style.width = '100%';
    overlay.style.height = '100%';
    overlay.style.backgroundColor = 'rgba(255, 215, 0, 0.3)'; // Gold color with transparency
    overlay.style.zIndex = '9999';
    overlay.style.pointerEvents = 'none';
    document.body.appendChild(overlay);
    
    setTimeout(() => {
        document.body.removeChild(overlay);
    }, 300);
}

// Modify the Konami code event listener
document.addEventListener('keydown', function(e) {
    if (e.code === konamiCode[konamiIndex]) {
        konamiIndex++;
        
        // Flash the screen for each correct key
        flashScreen();
        
        if (konamiIndex === konamiCode.length) {
            konamiIndex = 0;
            window.location.href = '/arr';
        }
    } else {
        konamiIndex = 0;
    }
});
```

### 4. Add a Hint on the Homepage

To subtly hint at the existence of the easter egg, I'll add a small indicator on the homepage:

```html
<!-- Add to the bottom of mode_selection.html -->
<div style="position: fixed; bottom: 10px; right: 10px; font-size: 12px; color: rgba(255, 215, 0, 0.5);">
    ↑↑↓↓←→←→BA
</div>
```

## Game Description

The ARR game is a strategic management simulation where:

1. Players start with a random initial ARR between 1,000,000€ and 5,000,000€
2. The goal is to increase ARR by at least 15% within 12 months
3. Each month, players can take one strategic action (marketing campaign, product improvement, etc.)
4. Random events (economic crisis, market opportunities, etc.) will affect ARR
5. If the 15% target is reached, employees receive bonuses; otherwise, no one gets a bonus

## How to Access the Easter Egg

1. Go to the homepage (mode selection page)
2. Enter the Konami code: ↑↑↓↓←→←→BA (arrow keys followed by B and A keys)
3. The screen will flash gold with each correct key press
4. After entering the full sequence, you'll be redirected to the ARR game introduction
5. Click "Commencer" to start the game

This implementation creates an engaging easter egg that's hidden but discoverable, with a game that ties directly to the business concept of ARR and employee bonuses.