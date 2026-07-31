import * as setup from "./utils/setup.js";

// Each test starts from a single recommendation at score 0. The suite used to
// share one row across all four tests and assert on the score left behind by
// the previous one, which made every failure cascade.
describe("E2E tests: POST voting", () => {
    let song;

    beforeEach(() => {
        cy.resetPosts();
        song = setup.createRecommendation();
        cy.createPost(song);
    });

    it("Upvote a song", () => {
        cy.visit("/");
        cy.get('[data-identifier="vote-menu"]').should("have.text", "0");

        cy.intercept("POST", "/recommendations/*/upvote").as("upvoteSong");
        cy.get('[data-identifier="upvote"]').click();
        cy.wait("@upvoteSong");

        cy.get('[data-identifier="vote-menu"]').should("have.text", "1");
    });

    it("Upvote a song 3x", () => {
        cy.visit("/");
        cy.get('[data-identifier="vote-menu"]').should("have.text", "0");

        for (let i = 0; i < 3; i++) {
            cy.intercept("POST", "/recommendations/*/upvote").as("upvoteSong");
            cy.get('[data-identifier="upvote"]').click();
            cy.wait("@upvoteSong");
            cy.get('[data-identifier="vote-menu"]').should("have.text", `${i + 1}`);
        }
    });

    it("Downvote a song 3x", () => {
        cy.visit("/");
        cy.get('[data-identifier="vote-menu"]').should("have.text", "0");

        for (let i = 0; i < 3; i++) {
            cy.intercept("POST", "/recommendations/*/downvote").as("downvoteSong");
            cy.get('[data-identifier="downvote"]').click();
            cy.wait("@downvoteSong");
            cy.get('[data-identifier="vote-menu"]').should("have.text", `${-1 - i}`);
        }
    });

    it("Downvote: votes < -5 ? <delete_song> : <downvote>", () => {
        cy.visit("/");
        cy.get('[data-identifier="vote-menu"]').should("have.text", "0");

        for (let i = 0; i < 6; i++) {
            cy.intercept("POST", "/recommendations/*/downvote").as("downvoteSong");
            cy.get('[data-identifier="downvote"]').click();
            cy.wait("@downvoteSong");
        }

        // The service removes a recommendation once its score drops below -5.
        cy.contains(song.name).should("not.exist");
    });
});
