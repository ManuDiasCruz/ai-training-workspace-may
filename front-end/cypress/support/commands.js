const apiUrl = () => Cypress.env("apiUrl") || "http://localhost:5000";

// Wipes the recommendations table (back-end must run with MODE=TEST).
Cypress.Commands.add("resetData", () => {
  cy.request("DELETE", `${apiUrl()}/tests/reset`);
});
Cypress.Commands.add("resetPosts", () => {
  cy.resetData();
});

// Creates a recommendation through the public API.
Cypress.Commands.add("addSong", (song) => {
  cy.request("POST", `${apiUrl()}/recommendations`, song);
});
Cypress.Commands.add("createPost", (song) => {
  cy.addSong(song);
});

// Bulk-inserts `amount` recommendations; `highScorePercentage`% of them get a
// score above 10 (back-end must run with MODE=TEST).
Cypress.Commands.add("seedDatabase", (amount, highScorePercentage = 0) => {
  cy.request("POST", `${apiUrl()}/tests/seed`, { amount, highScorePercentage });
});
