const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: "http://localhost:3000",
    specPattern: "cypress/e2e/spec.recommendation.cy.js",
    setupNodeEvents(on, config) {
      // implement node event listeners here
    },
  },
  env: { apiUrl: "http://localhost:5000" },
  video: false,
});
