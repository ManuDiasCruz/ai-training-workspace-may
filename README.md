# Parrot Card Game

Parrot Card Game is a browser-based memory game. At the start of each round, the player chooses an even number of cards between 4 and 14, then flips cards two at a time to find matching animated parrots.

## Local Setup

The project is a static HTML, CSS, and JavaScript application with no build step.

1. Clone the repository.
2. Start a local static server from the project root:

   ```bash
   python3 -m http.server 8000
   ```

3. Open [http://localhost:8000](http://localhost:8000) in a browser.
4. Enter an even card count between 4 and 14 when prompted.

## UI And Responsiveness Improvements

- Replaced the fixed-margin card layout with a centered responsive grid.
- Added a compact three-column mobile layout so the game remains practical on narrow screens.
- Standardized the visible palette to white, light green, and black text.
- Grouped the title and game status in a consistent light-green header.
- Added keyboard activation for cards with `Enter` and `Space`.
- Prevented a player from matching a card with itself and clarified timer reset behavior between rounds.

## Known Limitations

- The card-count and replay flows still use native browser prompts.
- Game progress is not persisted after a page refresh.
- The interface text is currently available in Portuguese only.
