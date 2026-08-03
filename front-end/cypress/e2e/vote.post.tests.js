import * as setup from "./utils/setup.js";

// The suite used a single `before` hook and then leaked score state between
// tests ("Upvote a song 3x" assumed the previous test had left the score at 1),
// while its last test reset the database halfway through the run. Each test now
// starts from a truncated table with exactly one song, whose id is 1 because
// the reset does TRUNCATE ... RESTART IDENTITY.
let song;

beforeEach(() => {
    cy.resetPosts();
    song = setup.createRecommendation();
    cy.createPost(song);
});

describe("E2E tests: POST voting", () => {
    it("Upvote a song", () => {
        cy.visit("/");
        cy.get('[data-identifier="score"]').should("have.text", "0");

        cy.intercept("POST", "**/recommendations/1/upvote").as("upvoteSong");
        cy.get('[data-identifier="upvote"]').click();
        cy.wait("@upvoteSong");

        cy.get('[data-identifier="score"]').should("have.text", "1");
    });

    it("Upvote a song 3x", () => {
        cy.visit("/");
        cy.get('[data-identifier="score"]').should("have.text", "0");

        for (let i = 0; i < 3; i++) {
            cy.intercept("POST", "**/recommendations/1/upvote").as("upvoteSong");
            cy.get('[data-identifier="upvote"]').click();
            cy.wait("@upvoteSong");
            cy.get('[data-identifier="score"]').should("have.text", `${i + 1}`);
        }

        cy.get('[data-identifier="score"]').should("have.text", "3");
    });

    it("Downvote a song 3x", () => {
        cy.visit("/");
        cy.get('[data-identifier="score"]').should("have.text", "0");

        for (let i = 0; i < 3; i++) {
            cy.intercept("POST", "**/recommendations/1/downvote").as("downvoteSong");
            cy.get('[data-identifier="downvote"]').click();
            cy.wait("@downvoteSong");
            cy.get('[data-identifier="score"]').should("have.text", `${-1 - i}`);
        }
    });

    // The song is removed once its score drops below -5, i.e. on the 6th
    // downvote. The original test referenced an undefined `musicData` variable.
    it("Downvote: votes < -5 ? <delete_song> : <downvote>", () => {
        cy.visit("/");

        for (let i = 0; i < 6; i++) {
            cy.get('[data-identifier="score"]').should("have.text", `${-i}`);
            cy.intercept("POST", "**/recommendations/1/downvote").as("downvoteSong");
            cy.get('[data-identifier="downvote"]').click();
            cy.wait("@downvoteSong");
        }

        cy.contains(song.name).should("not.exist");
        cy.get('[data-identifier="empty-state"]').should("be.visible");
    });
});
