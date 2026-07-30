const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    // Lets the specs use cy.visit("/") instead of hardcoding the host.
    // Override with CYPRESS_BASE_URL when the app runs elsewhere.
    baseUrl: process.env.CYPRESS_BASE_URL || "http://localhost:3000",

    // `utils/` holds shared helpers, not specs - without this Cypress tries to
    // run setup.js as a spec and fails because it contains no tests.
    specPattern: "cypress/e2e/**/*.cy.{js,jsx,ts,tsx}",
    excludeSpecPattern: ["cypress/e2e/utils/**"],

    env: {
      // The API must be running with MODE=TEST so DELETE /tests/reset exists.
      apiUrl: process.env.CYPRESS_API_URL || "http://localhost:5000",
    },

    setupNodeEvents(on, config) {
      return config;
    },
  },
});
