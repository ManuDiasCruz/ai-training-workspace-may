const apiUrl = () => Cypress.env("apiUrl");

// The specs referenced cy.resetPosts, cy.seedDatabase and cy.createPost, none
// of which existed, and the one command that did exist pointed at /reset
// instead of /tests/reset (the router is mounted under /tests, and only while
// the API runs with MODE=TEST).

Cypress.Commands.add("resetData", () => {
    cy.request("DELETE", `${apiUrl()}/tests/reset`);
});

// Alias: the specs use both names interchangeably.
Cypress.Commands.add("resetPosts", () => {
    cy.resetData();
});

Cypress.Commands.add("addSong", (song) => {
    cy.request("POST", `${apiUrl()}/recommendations`, song);
});

// Alias for the same reason as resetPosts.
Cypress.Commands.add("createPost", (song) => {
    cy.addSong(song);
});

Cypress.Commands.add("seedDatabase", (amount, highScorePercentage = 0) => {
    cy.request("POST", `${apiUrl()}/tests/seed`, { amount, highScorePercentage });
});
