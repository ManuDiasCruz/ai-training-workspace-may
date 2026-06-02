# Parrot Card Game

A browser-based memory card game built with plain HTML, CSS, and JavaScript. The player chooses an even number of cards between 4 and 14, flips two cards at a time, and wins when all matching parrot pairs are found.

This branch imports and updates the original project from [ManuDiasCruz/parrots-memory-card-game](https://github.com/ManuDiasCruz/parrots-memory-card-game).

## Local Setup

No package installation or build step is required.

1. Start a local static server from the project root:

   ```bash
   python3 -m http.server 8000
   ```

2. Open the game in a browser:

   ```text
   http://localhost:8000/
   ```

3. Enter an even card count between 4 and 14 when prompted.

For preview automation or screenshots, pass a valid card count in the URL to skip the startup prompt:

```text
http://localhost:8000/?cards=14
```

## UI And Responsiveness Improvements

- Reworked the layout around a centered header, compact scoreboard, and responsive card grid.
- Replaced fixed desktop margins with fluid spacing, max-width containers, and mobile-specific card sizing.
- Updated the visual palette so the application chrome consistently uses white, light green, and black text/borders.
- Improved card styling with consistent borders, rounded corners, focus states, and scalable image sizing.
- Removed the external font dependency so the game remains lightweight and reliable offline.
- Tightened card interaction behavior by preventing the same card or already matched cards from being selected again.

## Known Limitations

- The original animated parrot artwork keeps its source colors; the requested white/light-green/black palette is applied to the surrounding UI.
- The game still uses browser prompts and alerts for setup and end-of-game flow to preserve the original behavior.
- There is no automated test suite; validation is currently done with browser smoke tests and responsive screenshots.
