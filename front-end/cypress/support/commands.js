Cypress.Commands.add("resetRecommendations", () => {
  cy.request("DELETE", `${Cypress.env("apiUrl")}/tests/reset`);
});

Cypress.Commands.add("addRecommendation", (recommendation) => {
  cy.request(
    "POST",
    `${Cypress.env("apiUrl")}/recommendations`,
    recommendation
  );
});
