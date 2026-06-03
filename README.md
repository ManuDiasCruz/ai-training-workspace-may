# Parrot Card Game

## Project Overview

Parrot Card Game is a browser-based memory matching game built with plain HTML, CSS, and JavaScript. The player chooses an even number of cards between 4 and 14, flips cards to find matching parrot pairs, and tracks both moves and elapsed time.

## Local Setup

1. Clone the repository.
2. Open `index.html` directly in a browser, or run a simple static server from the project root:

```bash
python3 -m http.server 8000
```

3. Open `http://localhost:8000` in the browser.

## UI And Responsiveness Improvements

- Reworked the layout to use a centered responsive grid instead of fixed margins.
- Added a compact mobile layout that shows three columns of cards on smaller screens.
- Kept the app visually consistent with a white and light-green palette plus black text.
- Updated the header and game stats area to stay readable on desktop and mobile widths.
- Fixed card-selection behavior so clicking the same card twice does not count as a match.

## Known Limitations

- Card count and replay flows still use native browser prompts and alerts.
- The game is a single static page and does not persist progress between page reloads.
