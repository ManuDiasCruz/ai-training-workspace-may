const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    // Front-end origin under test. Override with CYPRESS_BASE_URL.
    baseUrl: "http://localhost:3000",
    env: {
      // Back-end API origin. Override with CYPRESS_API_URL. When the app is
      // served behind a same-origin proxy, point this at the front-end origin.
      apiUrl: "http://localhost:5000",
    },
    setupNodeEvents(on, config) {
      config.baseUrl = process.env.CYPRESS_BASE_URL || config.baseUrl;
      config.env.apiUrl = process.env.CYPRESS_API_URL || config.env.apiUrl;
      return config;
    },
  },
});
