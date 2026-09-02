/// <reference types="cypress" />

import * as setup from "./utils/setup.js";

before(() => {
  cy.resetPosts();
  const song = setup.createRecommendation();
  cy.createPost(song);
});

describe("E2E tests: POST voting", () => {
  it("Upvote a song", () => {
    cy.visit("/");

    cy.intercept("POST", "/recommendations/1/upvote").as("upvoteSong");
    cy.get('[data-identifier="upvote"]').click();
    cy.wait("@upvoteSong");

    cy.get('[data-identifier="vote-menu"]').should("have.text", "1");
  });

  it("Upvote a song 3x", () => {
    cy.visit("/");
    cy.get('[data-identifier="vote-menu"]').should("have.text", "1");

    for (let i = 0; i < 3; i++) {
      cy.intercept("POST", "/recommendations/1/upvote").as("upvoteSong");
      cy.get('[data-identifier="upvote"]').click();
      cy.wait("@upvoteSong");
    }

    cy.get('[data-identifier="vote-menu"]').should("have.text", "4");
  });

  it("Downvote a song 3x", () => {
    cy.visit("/");
    cy.get('[data-identifier="vote-menu"]').should("have.text", "4");

    for (let i = 0; i < 3; i++) {
      cy.intercept("POST", "/recommendations/1/downvote").as("downvoteSong");
      cy.get('[data-identifier="downvote"]').click();
      cy.wait("@downvoteSong");
      cy.get('[data-identifier="vote-menu"]').should("have.text", `${3 - i}`);
    }
  });

  it("Downvote: votes < -5 ? <delete_song> : <downvote>", () => {
    cy.resetPosts();
    const song = setup.createRecommendation();
    cy.addSong(song);

    cy.visit("/");
    for (let i = 0; i < 6; i++) {
      cy.get('[data-identifier="vote-menu"]').should("have.text", `${0 - i}`);
      cy.intercept("POST", "/recommendations/1/downvote").as("downvoteSong");
      cy.get('[data-identifier="downvote"]').click();
      cy.wait("@downvoteSong");
    }

    cy.contains(song.name).should("not.exist");
    cy.contains("No recommendations yet!").should("exist");
  });
});
