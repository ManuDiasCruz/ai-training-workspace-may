const { defineConfig } = require("cypress");
module.exports = defineConfig({
  e2e: {
    baseUrl: process.env.CYPRESS_BASE_URL || "http://localhost:5000",
    specPattern: "cypress/e2e/spec.recommendation.cy.js",
    supportFile: false,
  },
  video: false,
});
