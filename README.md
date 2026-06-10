# Parrot Memory

Parrot Memory is a browser-based matching game built with plain HTML, CSS, and JavaScript. Players can choose between 4 and 14 cards, match animated parrot pairs, and track moves, elapsed time, and completed pairs.

## Local setup

No package installation or build step is required.

1. Clone the repository and switch to the project branch:

   ```bash
   git clone https://github.com/ManuDiasCruz/ai-training-workspace-may.git
   cd ai-training-workspace-may
   git switch kindle-alpha-parrot-memo-game
   ```

2. Start a local static server:

   ```bash
   python3 -m http.server 8000
   ```

3. Open `http://localhost:8000` in a modern browser.

Opening `index.html` directly also works, but a local server provides behavior closer to a deployed static site.

## UI and responsiveness improvements

- Replaced browser prompts and alerts with an in-page card-count control and win dialog.
- Added a responsive three-column mobile board that remains usable down to 280px wide.
- Added a flexible desktop grid that adapts to the selected card count.
- Standardized the interface to white, light green, and black text and controls.
- Added consistent spacing, borders, focus states, and card proportions across screen sizes.
- Improved keyboard accessibility by rendering cards as native buttons.
- Fixed duplicate-card selection, input locking during mismatches, timer reset, and restart behavior.
- Added live move, timer, and matched-pair status.
- Added reduced-motion support for users who request it in their operating system.

## Validation

The game was verified in headless Chrome at desktop and mobile viewport sizes, including 1440x900, 360x800, and 280x720. Checks covered horizontal overflow, card-count changes, duplicate clicks, pair matching, the completed-game dialog, and the requested UI color palette.

## Known limitations

- The game relies on the browser's native `dialog` element and is intended for current versions of Chrome, Edge, Firefox, and Safari.
- The original animated parrot artwork retains its own colors; the white, light green, and black palette applies to the application interface.
- The project does not currently include a committed automated test suite.
