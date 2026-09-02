const apiUrl = (path) => `${Cypress.env("apiUrl")}${path}`;

// The reset route lives under /tests and is only mounted when the API runs
// with MODE=TEST (see back-end/src/app.ts).
Cypress.Commands.add("resetData", () => {
  cy.request("DELETE", apiUrl("/tests/reset"));
});

// The specs were written against both names; keep them as aliases so either
// spelling works.
Cypress.Commands.add("resetPosts", () => {
  cy.resetData();
});

Cypress.Commands.add("addSong", (song) => {
  cy.request("POST", apiUrl("/recommendations"), song);
});

Cypress.Commands.add("createPost", (song) => {
  cy.addSong(song);
});

// Bulk-inserts songs with predefined scores, which the public API cannot do.
Cypress.Commands.add("seedDatabase", (amount, highScorePercentage) => {
  cy.request("POST", apiUrl("/tests/seed"), { amount, highScorePercentage });
});
