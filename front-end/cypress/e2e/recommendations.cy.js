/// <reference types="cypress" />

const song = {
  name: "Mundo Bita - O Circo chegou",
  youtubeLink: "https://www.youtube.com/watch?v=qmUQr3zrqXM",
};

describe("recommendation flows", () => {
  beforeEach(() => cy.resetData());

  it("creates, votes, and displays a recommendation on each timeline", () => {
    cy.intercept("POST", "**/recommendations").as("create");
    cy.visit("/");
    cy.get('[aria-label="Recommendation name"]').type(song.name);
    cy.get('[aria-label="YouTube URL"]').type(song.youtubeLink);
    cy.get('[aria-label="Create recommendation"]').click();
    cy.wait("@create").its("response.statusCode").should("eq", 201);
    cy.contains(song.name).should("be.visible");

    cy.intercept("POST", "**/recommendations/*/upvote").as("upvote");
    cy.get('[data-identifier="upvote"]').click();
    cy.wait("@upvote").its("response.statusCode").should("eq", 200);
    cy.get('[data-identifier="score"]').should("have.text", "1");

    cy.contains("Top").click();
    cy.contains(song.name).should("be.visible");
    cy.contains("Random").click();
    cy.contains(song.name).should("be.visible");
  });

  it("retains input and shows an error when the API rejects a URL", () => {
    cy.intercept("POST", "**/recommendations").as("create");
    cy.visit("/");
    cy.get('[aria-label="Recommendation name"]').type("Invalid link");
    cy.get('[aria-label="YouTube URL"]').type("https://example.com/video");
    cy.get('[aria-label="Create recommendation"]').click();
    cy.wait("@create").its("response.statusCode").should("eq", 422);
    cy.contains("Could not create that recommendation").should("be.visible");
    cy.get('[aria-label="Recommendation name"]').should("have.value", "Invalid link");
  });

  it("shows the random empty state", () => {
    cy.visit("/random");
    cy.contains("No recommendations yet").should("be.visible");
  });
});
