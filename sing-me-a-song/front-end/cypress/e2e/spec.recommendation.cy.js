/// <reference types="cypress" />
const song = { name: "Cypress song", youtubeLink: "https://youtu.be/dQw4w9WgXcQ" };
const submit = () => {
  cy.get('[aria-label="Name"]').type(song.name);
  cy.get('[aria-label="YouTube link"]').type(song.youtubeLink);
  cy.get('[aria-label="Create recommendation"]').click();
};
describe("Recommendation flows against the real API", () => {
  beforeEach(() => { cy.request("DELETE", "/tests/reset"); });
  it("creates, ranks, randomly selects, votes and deletes below -5", () => {
    cy.visit("/");
    cy.contains("No recommendations yet");
    submit();
    cy.get("article").should("contain", song.name);
    cy.get('[aria-label="Upvote Cypress song"]').click();
    cy.get("article").should("contain", "1");
    cy.visit("/top");
    cy.get("article").should("contain", song.name);
    cy.visit("/random");
    cy.get("article").should("contain", song.name);
    for(let i=0;i<7;i++) {
      cy.intercept("POST", "**/api/recommendations/*/downvote").as(`vote${i}`);
      cy.get('[aria-label="Downvote Cypress song"]').should("be.enabled").click();
      cy.wait(`@vote${i}`).its("response.statusCode").should("eq", 200);
      if(i<6) cy.get("article").should("contain", String(-i));
    }
    cy.contains("No recommendations yet");
    cy.request("/api/recommendations").its("body").should("have.length", 0);
  });
  it("keeps duplicate input and shows server validation errors", () => {
    cy.request("POST", "/api/recommendations", song);
    cy.visit("/");
    submit();
    cy.get('[role="alert"]').should("contain", "already exists");
    cy.get('[aria-label="Name"]').should("have.value", song.name);
    cy.get('[aria-label="YouTube link"]').clear().type("https://example.com/not-youtube");
    cy.get('[aria-label="Create recommendation"]').click();
    cy.get('[role="alert"]').should("contain", "valid YouTube");
  });
  it("shows a retry after an API failure", () => {
    cy.intercept("GET", "**/api/recommendations", {times: 1, statusCode: 503, body: "Unavailable"});
    cy.visit("/");
    cy.contains("Could not load recommendations");
    cy.contains("button", "Retry").click();
    cy.contains("No recommendations yet");
  });
});
