const { defineConfig } = require("cypress");

// The specs used to hardcode http://localhost:3000 in every cy.visit and
// http://localhost:5000 in every cy.request, and the default specPattern only
// matches *.cy.{js,jsx,ts,tsx} - so the real spec files, all named *.tests.js,
// were silently never executed. Both are fixed here.
module.exports = defineConfig({
  e2e: {
    baseUrl: process.env.CYPRESS_BASE_URL || "http://localhost:3000",
    specPattern: "cypress/e2e/**/*.{cy,tests}.{js,jsx,ts,tsx}",
    supportFile: "cypress/support/e2e.js",
    video: false,
    defaultCommandTimeout: 8000,
    env: {
      // Base URL of the API. Must be the same instance the front-end talks to,
      // and it has to be running with MODE=TEST so that /tests/* is mounted.
      apiUrl: process.env.CYPRESS_API_URL || "http://localhost:5000"
    },
    setupNodeEvents(on, config) {
      return config;
    },
  },
});
