import { createRecommendation } from "../e2e/utils/setup";

// Base URL of the API under test. Override with CYPRESS_API_BASE_URL when the
// back-end does not run on the default port.
const API = Cypress.env("API_BASE_URL") || "http://localhost:5000";

// DELETE /tests/reset is only mounted when the API runs with MODE=TEST.
Cypress.Commands.add("resetPosts", () => {
  cy.request("DELETE", `${API}/tests/reset`);
});

// Alias kept because some specs referred to this name.
Cypress.Commands.add("resetData", () => {
  cy.resetPosts();
});

Cypress.Commands.add("addSong", (song) => {
  cy.request("POST", `${API}/recommendations`, song);
});

Cypress.Commands.add("createPost", (song) => {
  cy.addSong(song);
});

// Inserts `amount` recommendations, then pushes `highScorePercentage` of them
// above the score > 10 threshold that GET /recommendations/random filters on.
Cypress.Commands.add("seedDatabase", (amount, highScorePercentage = 0) => {
  for (let i = 0; i < amount; i += 1) {
    cy.request("POST", `${API}/recommendations`, createRecommendation());
  }

  const highScoreCount = Math.round((amount * highScorePercentage) / 100);
  if (highScoreCount === 0) return;

  // POST /recommendations answers 201 with an empty body, so the ids have to
  // be read back. top/:amount returns every row when amount >= the row count.
  cy.request("GET", `${API}/recommendations/top/${amount}`).then(({ body }) => {
    body.slice(0, highScoreCount).forEach(({ id }) => {
      for (let vote = 0; vote < 11; vote += 1) {
        cy.request("POST", `${API}/recommendations/${id}/upvote`);
      }
    });
  });
});
