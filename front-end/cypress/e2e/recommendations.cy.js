/// <reference types="cypress" />

const song = {
  name: "Mundo Bita - O Circo chegou",
  youtubeLink: "https://www.youtube.com/watch?v=qmUQr3zrqXM",
};

describe("recommendation flow", () => {
  beforeEach(() => cy.resetData());

  it("creates, votes, and displays a recommendation across the views", () => {
    cy.intercept("POST", "**/recommendations").as("create");
    cy.visit("/");
    cy.get('input[aria-label="Recommendation name"]').type(song.name);
    cy.get('input[aria-label="YouTube link"]').type(song.youtubeLink);
    cy.get('button[aria-label="Create recommendation"]').click();
    cy.wait("@create").its("response.statusCode").should("eq", 201);
    cy.contains(song.name).should("be.visible");

    cy.intercept("POST", "**/recommendations/*/upvote").as("upvote");
    cy.get('[data-identifier="upvote"]').click();
    cy.wait("@upvote").its("response.statusCode").should("eq", 200);
    cy.get('[data-identifier="vote-menu"]').should("contain", "1");

    cy.contains("Top").click();
    cy.contains(song.name).should("be.visible");
    cy.contains("Random").click();
    cy.contains(song.name).should("be.visible");
  });

  it("shows an empty random state instead of loading forever", () => {
    cy.visit("/random");
    cy.contains("No recommendations yet").should("be.visible");
  });

  it("keeps form values and shows an error for a duplicate name", () => {
    cy.addSong(song);
    cy.visit("/");
    cy.get('input[aria-label="Recommendation name"]').type(song.name);
    cy.get('input[aria-label="YouTube link"]').type(song.youtubeLink);
    cy.get('button[aria-label="Create recommendation"]').click();
    cy.get('[role="alert"]').should("contain", "Could not create recommendation");
    cy.get('input[aria-label="Recommendation name"]').should("have.value", song.name);
  });
});
