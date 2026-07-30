import * as setup from "./utils/setup.js";

// The tests below run against a single recommendation and accumulate its score,
// so the fixture is created once for the whole file.
before(() => {
    cy.resetPosts();
    cy.createPost(setup.createRecommendation());
});

// Reading the score through its own data-identifier is stable across the
// re-render that follows each vote. The previous `cy.contains("0").as("votes")`
// aliased whichever element happened to hold the old score text, so the alias
// no longer resolved once the number changed.
const score = () => cy.get('[data-identifier="score"]').first();

describe("E2E tests: POST voting", () => {
    it("Upvote a song", () => {
        cy.visit("/");

        cy.intercept("POST", "/recommendations/1/upvote").as("upvoteSong");
        cy.get('[data-identifier="upvote"]').click();
        cy.wait("@upvoteSong");

        score().should("have.text", "1");
    });

    it("Upvote a song 3x", () => {
        cy.visit("/");
        score().should("have.text", "1");

        for (let i = 0; i < 3; i++) {
            cy.intercept("POST", "/recommendations/1/upvote").as("upvoteSong");
            cy.get('[data-identifier="upvote"]').click();
            cy.wait("@upvoteSong");
        }

        score().should("have.text", "4");
    });

    it("Downvote a song 3x", () => {
        cy.visit("/");
        score().should("have.text", "4");

        // Asserted `4 - i` after the click, so the very first iteration expected
        // the pre-click value. The score is 3 after one downvote, not 4.
        for (let i = 0; i < 3; i++) {
            cy.intercept("POST", "/recommendations/1/downvote").as("downvoteSong");
            cy.get('[data-identifier="downvote"]').click();
            cy.wait("@downvoteSong");
            score().should("have.text", `${3 - i}`);
        }
    });

    it("Downvote: votes < -5 ? <delete_song> : <downvote>", () => {
        cy.resetPosts();
        const song = setup.createRecommendation();
        cy.addSong(song);

        cy.visit("/");
        for (let i = 0; i < 6; i++) {
            score().should("have.text", `${0 - i}`);
            cy.intercept("POST", "/recommendations/1/downvote").as("downvoteSong");
            cy.get('[data-identifier="downvote"]').click();
            cy.wait("@downvoteSong");
        }

        // Referenced an undefined `musicData` here, which threw before the
        // assertion could run.
        cy.contains(song.name).should("not.exist");
    });
});
