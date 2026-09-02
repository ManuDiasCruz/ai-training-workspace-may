describe("Sing Me a Song main flow", () => {
  const song = {
    name: "Mundo Bita - O Circo Chegou",
    youtubeLink: "https://www.youtube.com/watch?v=qmUQr3zrqXM",
  };

  beforeEach(() => {
    cy.resetData();
  });

  it("creates, displays, votes, and navigates between recommendations", () => {
    cy.intercept("POST", "**/recommendations").as("createRecommendation");
    cy.visit("/");
    cy.get("input[placeholder='Name']").type(song.name);
    cy.get("input[placeholder='https://youtu.be/...']").type(song.youtubeLink);
    cy.get("button[aria-label='Create recommendation']").click();

    cy.wait("@createRecommendation").its("response.statusCode").should("equal", 201);
    cy.contains(song.name).should("be.visible");

    cy.intercept("POST", "**/recommendations/*/upvote").as("upvoteRecommendation");
    cy.get("button[data-identifier='upvote']").click();
    cy.wait("@upvoteRecommendation").its("response.statusCode").should("equal", 200);
    cy.get("[data-identifier='score']").should("have.text", "1");

    cy.contains("Top").click();
    cy.url().should("include", "/top");
    cy.contains(song.name).should("be.visible");

    cy.contains("Random").click();
    cy.url().should("include", "/random");
    cy.contains(song.name).should("be.visible");
  });
});
