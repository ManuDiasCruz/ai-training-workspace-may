const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: process.env.CYPRESS_BASE_URL || "http://localhost:3000",
    env: {
      apiUrl: process.env.CYPRESS_API_URL || "http://localhost:5000",
    },
    specPattern: "cypress/e2e/app.cy.js",
  },
  video: false,
});
