const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    // Specs used to hard-code http://localhost:3000 in every cy.visit.
    // Override with CYPRESS_BASE_URL when the dev server runs elsewhere.
    baseUrl: process.env.CYPRESS_BASE_URL || "http://localhost:3000",
    video: false,
    env: {
      API_BASE_URL: process.env.CYPRESS_API_BASE_URL || "http://localhost:5000",
    },
    setupNodeEvents(on, config) {
      return config;
    },
  },
});
