// Base URL of the API under test. Override with CYPRESS_apiUrl or the `env`
// block in cypress.config.js when the API does not run on the default port.
const apiUrl = () => Cypress.env("apiUrl");

// Wipes the recommendations table. This requires the API to be running with
// MODE=TEST, which is what `npm run dev:test` in back-end does - otherwise the
// /tests router is never mounted.
Cypress.Commands.add("resetData", () => {
    cy.request("DELETE", `${apiUrl()}/tests/reset`);
});

// Kept as an alias because the specs were written against both names.
Cypress.Commands.add("resetPosts", () => {
    cy.resetData();
});

Cypress.Commands.add("addSong", (song) => {
    cy.request("POST", `${apiUrl()}/recommendations`, song);
});

Cypress.Commands.add("createPost", (song) => {
    cy.addSong(song);
});

// `name` is unique, so seeded songs are numbered across every call within a run
// rather than per call - otherwise a second cy.seedDatabase() collides with the
// first and cy.request fails on the 409.
let seedCounter = 0;

// Creates `amount` recommendations, `highScorePercentage`% of which are pushed
// above the score-10 threshold that GET /recommendations/random filters on.
Cypress.Commands.add("seedDatabase", (amount, highScorePercentage = 0) => {
    const highScoreCount = Math.round((amount * highScorePercentage) / 100);

    for (let i = 0; i < amount; i++) {
        seedCounter += 1;

        const song = {
            name: `seeded song ${seedCounter}`,
            youtubeLink: `https://www.youtube.com/watch?v=seeded${seedCounter}`,
        };

        cy.request("POST", `${apiUrl()}/recommendations`, song);
    }

    if (highScoreCount === 0) return;

    // Read the ids back once, then push the first slice above the score
    // threshold that GET /recommendations/random filters on.
    cy.request("GET", `${apiUrl()}/recommendations/top/${amount}`).then(({ body }) => {
        body.slice(0, highScoreCount).forEach((recommendation) => {
            for (let vote = 0; vote < 11; vote++) {
                cy.request("POST", `${apiUrl()}/recommendations/${recommendation.id}/upvote`);
            }
        });
    });
});
