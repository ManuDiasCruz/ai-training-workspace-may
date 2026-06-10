const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    // Where the React app is served. Override with CYPRESS_BASE_URL.
    baseUrl: "http://localhost:3000",
    env: {
      // Where the API is served. Override with CYPRESS_apiUrl.
      // The backend must run with MODE=TEST so DELETE /tests/reset exists.
      apiUrl: "http://localhost:5000",
    },
    video: false,
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
});
