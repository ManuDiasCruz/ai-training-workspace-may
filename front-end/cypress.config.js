const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    // Front-end under test. Override with CYPRESS_BASE_URL=...
    baseUrl: "http://localhost:3000",
    env: {
      // Back-end API. It must run with MODE=TEST (npm run dev:test) so the
      // /tests/reset and /tests/seed helpers are available.
      // Override with CYPRESS_apiUrl=...
      apiUrl: "http://localhost:5000",
    },
    video: false,
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
});
