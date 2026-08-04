const { defineConfig } = require("cypress");

module.exports = defineConfig({
  e2e: {
    baseUrl: "http://localhost:3000",
    env: {
      apiUrl: "http://localhost:5000",
    },
  },
});
