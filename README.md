# Parrot Card Game

Parrot Card Game is a browser-based memory card game. Players choose an even number of cards, reveal two cards at a time, and try to match every parrot pair with the fewest moves.

## Local Setup

This project is a static HTML, CSS, and JavaScript app. It does not require a package manager or build step.

1. From the project root, start a local static server:

   ```bash
   python3 -m http.server 8000
   ```

2. Open the game in a browser:

   ```text
   http://127.0.0.1:8000/
   ```

You can also open `index.html` directly, but using a local server better matches normal browser asset loading.

## UI And Responsiveness Updates

- Replaced blocking browser prompts with in-page card-count controls and a reusable New game action.
- Updated the application chrome to consistently use white, light green, and black text/borders.
- Added responsive layouts for desktop, tablet, and phone-sized screens.
- Reworked the card board with CSS Grid so cards stay centered and avoid horizontal overflow.
- Improved touch targets and focus states for the card-count controls and cards.
- Prevented selecting the same card twice as a pair.

## Known Limitations

The UI follows the requested white, light green, and black palette. The original animated parrot image assets still contain their own colors because they are the game content.
