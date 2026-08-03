/// <reference types="cypress" />

const recommendation = {
  name: "Mundo Bita - O Circo chegou",
  youtubeLink: "https://www.youtube.com/watch?v=qmUQr3zrqXM"
};

describe("Song recommendation flows", () => {
  beforeEach(() => {
    cy.resetData();
  });

  it("creates a recommendation from the home page", () => {
    cy.intercept("POST", "**/recommendations").as("createRecommendation");
    cy.visit("/");

    cy.get('input[placeholder="Name"]').type(recommendation.name);
    cy.get('input[placeholder="https://youtu.be/..."]').type(
      recommendation.youtubeLink
    );
    cy.get('button[aria-label="Create recommendation"]').click();

    cy.wait("@createRecommendation")
      .its("response.statusCode")
      .should("equal", 201);
    cy.contains(recommendation.name).should("be.visible");
  });

  it("rejects invalid YouTube links", () => {
    cy.intercept("POST", "**/recommendations").as("createRecommendation");
    cy.visit("/");

    cy.get('input[placeholder="Name"]').type("Invalid song");
    cy.get('input[placeholder="https://youtu.be/..."]').type("not-a-youtube-url");
    cy.get('button[aria-label="Create recommendation"]').click();

    cy.wait("@createRecommendation")
      .its("response.statusCode")
      .should("equal", 422);
  });

  it("upvotes and downvotes an existing recommendation", () => {
    cy.addSong(recommendation);
    cy.visit("/");

    cy.get('[data-identifier="upvote"]').click();
    cy.contains("1").should("be.visible");
    cy.get('[data-identifier="downvote"]').click();
    cy.contains("0").should("be.visible");
  });

  it("opens recommendations on the top and random routes", () => {
    cy.addSong(recommendation);

    cy.visit("/top");
    cy.contains(recommendation.name).should("be.visible");

    cy.visit("/random");
    cy.contains(recommendation.name).should("be.visible");
  });
});
