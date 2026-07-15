import { faker } from "@faker-js/faker";

import * as setup from "./utils/setup.js";

before(() => {
    cy.resetPosts();
});

describe("E2E tests: Render Screen", () => {
    it("Load 10 tests", () => {
        const amount = 100;
        const highScorePercentage = 70;
        cy.seedDatabase(amount, highScorePercentage);

        cy.intercept("GET", "/recommendations/random").as(
            "getRandomRecommendation"
        );

        cy.visit("http://localhost:3000/random");

        cy.wait("@getRandomRecommendation").then(({ response }) => {
            cy.log(response);
            expect(response.body).to.haveOwnProperty("name");
            expect(response.body).to.haveOwnProperty("youtubeLink");
            expect(response.body).to.haveOwnProperty("score");
        });
    });

    it("Load 10 random tests", () => {
        const amount = 50;
        const highScorePercentage = 100;
        cy.seedDatabase(amount, highScorePercentage);

        cy.intercept("GET", "/recommendations/top/10").as("getTopRecommendations");
        cy.visit("http://localhost:3000/top");
        cy.wait("@getTopRecommendations").then(({ response }) => {
            cy.log(response);
            expect(response.body.length).to.equal(10);
            expect(response.body[0]).to.haveOwnProperty("name");
            expect(response.body[0]).to.haveOwnProperty("youtubeLink");
            expect(response.body[0]).to.haveOwnProperty("score");
            expect(response.body[0].score).to.gte(response.body[9].score);
        });
    });
  });