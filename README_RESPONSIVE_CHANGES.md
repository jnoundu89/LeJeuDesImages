# Responsive Design Improvements for Larger Screens

This document outlines the changes made to improve the responsiveness of the application on screens larger than 1080p (1920x1080).

## Overview of Changes

Media queries for screens with a minimum width of 1921px have been added to the following CSS files:

1. `styles.css`
2. `homepage.css`
3. `normal-mode.css`
4. `score-section.css`

## Detailed Changes

### 1. styles.css

Added a media query for screens larger than 1080p that:
- Increases the maximum width of containers from 1200px to 1600px
- Increases the size of images (from 300px to 400px)
- Increases font sizes for better readability
- Adjusts spacing and dimensions of UI elements
- Increases the size of buttons and interactive elements

### 2. homepage.css

Added a media query for screens larger than 1080p that:
- Increases the maximum width of containers from 1200px to 1600px
- Increases the size of the game logo
- Increases font sizes for titles, taglines, and text
- Adjusts the grid layout for game modes to display larger cards
- Increases the size of buttons and interactive elements

### 3. normal-mode.css

Added a media query for screens larger than 1080p that:
- Increases the maximum height of the stats banner
- Increases the maximum width of images
- Increases the size of choice buttons

### 4. score-section.css

Added a media query for screens larger than 1080p that:
- Increases padding for the score section
- Increases font sizes for headings, scores, and text
- Adjusts margins and padding for better spacing

## Benefits

These changes ensure that the application is responsive and visually appealing on screens with resolutions higher than 1080p. The UI elements scale appropriately to make better use of the available screen space, improving the user experience on larger displays.