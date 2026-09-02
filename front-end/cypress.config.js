const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    // Lets the specs use cy.visit("/") instead of hardcoding the host.
    baseUrl: process.env.CYPRESS_BASE_URL || "http://localhost:3000",
    // The suite drives real HTTP against the API, so both URLs are needed.
    env: {
      apiUrl: process.env.CYPRESS_API_URL || "http://localhost:5000",
    },
    // The original suite named its files "*.tests.js", which the default
    // "*.cy.js" pattern never picked up, so none of them ever ran.
    specPattern: "cypress/e2e/**/*.cy.{js,jsx,ts,tsx}",
    video: false,
    setupNodeEvents(on, config) {
      return config;
    },
  },
});
