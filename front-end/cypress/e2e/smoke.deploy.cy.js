/// <reference types="cypress" />

import { faker } from "@faker-js/faker";

// Post-deployment smoke test: exercises create -> list -> upvote through the
// real UI without DELETE /tests/reset, so it can run against any environment:
//   CYPRESS_BASE_URL=https://app.example CYPRESS_apiUrl=https://api.example \
//     npx cypress run --spec cypress/e2e/smoke.deploy.cy.js
describe("Deployed stack smoke test", () => {
    it("create -> list -> upvote works end to end", () => {
        const name = `Deploy Smoke - ${faker.random.alphaNumeric(10)}`;
        const youtubeLink = "https://www.youtube.com/watch?v=qmUQr3zrqXM";

        cy.visit("/");

        cy.get("input[placeholder='Name']").type(name);
        cy.get("input[placeholder='https://youtu.be/...']").type(youtubeLink);

        cy.intercept("POST", "/recommendations").as("createRecommendation");
        cy.get("button").click();
        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(201);
        });

        // newest first: the recommendation we just created leads the feed
        cy.contains(name).should("exist");

        cy.intercept("POST", "/recommendations/*/upvote").as("upvoteSong");
        cy.get('[data-identifier="upvote"]').first().click();
        cy.wait("@upvoteSong").then((res) => {
            expect(res.response.statusCode).to.equals(200);
        });

        cy.get('[data-identifier="score"]').first().should("have.text", "1");
    });
});
