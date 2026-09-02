import * as setup from "./utils/setup.js";

// Each test starts from a clean database with a single song, so the specs no
// longer depend on the score left behind by the previous one. The reset
// restarts the identity sequence, so the song is always id 1.
describe("E2E tests: POST voting", () => {
    let song;

    beforeEach(() => {
        cy.resetPosts();
        song = setup.createRecommendation();
        cy.createPost(song);
        cy.visit("/");
    });

    it("Upvote a song", () => {
        cy.get('[data-identifier="score"]').should("have.text", "0");

        cy.intercept("POST", "/recommendations/1/upvote").as("upvoteSong");
        cy.get('[data-identifier="upvote"]').click();
        cy.wait("@upvoteSong");

        cy.get('[data-identifier="score"]').should("have.text", "1");
    });

    it("Upvote a song 3x", () => {
        for (let i = 0; i < 3; i++) {
            cy.intercept("POST", "/recommendations/1/upvote").as("upvoteSong");
            cy.get('[data-identifier="upvote"]').click();
            cy.wait("@upvoteSong");
            cy.get('[data-identifier="score"]').should("have.text", `${i + 1}`);
        }
    });

    it("Downvote a song 3x", () => {
        for (let i = 0; i < 3; i++) {
            cy.intercept("POST", "/recommendations/1/downvote").as("downvoteSong");
            cy.get('[data-identifier="downvote"]').click();
            cy.wait("@downvoteSong");
            cy.get('[data-identifier="score"]').should("have.text", `${-1 - i}`);
        }
    });

    it("Downvote: votes < -5 ? <delete_song> : <downvote>", () => {
        // The song survives down to -5 and is removed on the vote that would
        // take it to -6.
        for (let i = 0; i < 6; i++) {
            cy.intercept("POST", "/recommendations/1/downvote").as("downvoteSong");
            cy.get('[data-identifier="downvote"]').click();
            cy.wait("@downvoteSong");
        }

        cy.contains(song.name).should("not.exist");
        cy.contains("No recommendations yet!").should("be.visible");
    });
});
