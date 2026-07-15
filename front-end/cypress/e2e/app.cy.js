/// <reference types="cypress" />

describe("Sing me a Song", () => {
  const song = {
    name: "Mundo Bita - O Circo Chegou",
    youtubeLink: "https://www.youtube.com/watch?v=qmUQr3zrqXM",
  };

  beforeEach(() => {
    cy.resetData();
  });

  it("creates, lists, and votes on a recommendation", () => {
    cy.visit("/");
    cy.contains("No recommendations yet").should("be.visible");

    cy.intercept("POST", "**/recommendations").as("createRecommendation");
    cy.get("input[placeholder='Name']").type(song.name);
    cy.get("input[placeholder='https://youtu.be/...']").type(song.youtubeLink);
    cy.get("button[aria-label='Create recommendation']").click();

    cy.wait("@createRecommendation").its("response.statusCode").should("equal", 201);
    cy.contains(song.name).should("be.visible");

    cy.intercept("POST", "**/recommendations/*/upvote").as("upvoteRecommendation");
    cy.get("[data-identifier='upvote']").click();
    cy.wait("@upvoteRecommendation").its("response.statusCode").should("equal", 200);
    cy.get("[data-identifier='vote-menu']").should("contain.text", "1");
  });

  it("shows seeded recommendations on the top and random pages", () => {
    cy.addSong(song);

    cy.visit("/top");
    cy.contains(song.name).should("be.visible");

    cy.visit("/random");
    cy.contains(song.name).should("be.visible");
  });
});
