describe("Sing me a Song main flows", () => {
  beforeEach(() => {
    cy.resetRecommendations();
  });

  it("creates and upvotes a recommendation", () => {
    const name = "Mundo Bita - O Circo Chegou";

    cy.intercept("POST", "**/recommendations").as("createRecommendation");
    cy.visit("/");
    cy.get('[aria-label="Song name"]').type(name);
    cy.get('[aria-label="YouTube link"]').type(
      "https://www.youtube.com/watch?v=qmUQr3zrqXM"
    );
    cy.get('[aria-label="Add recommendation"]').click();

    cy.wait("@createRecommendation")
      .its("response.statusCode")
      .should("equal", 201);
    cy.contains(name).should("be.visible");

    cy.intercept("POST", "**/recommendations/*/upvote").as("upvote");
    cy.get(`[aria-label="Upvote ${name}"]`).click();
    cy.wait("@upvote").its("response.statusCode").should("equal", 200);
    cy.get('[data-identifier="vote-count"]').should("have.text", "1");
  });

  it("loads the top and random routes", () => {
    const recommendation = {
      name: "The Beatles - Here Comes the Sun",
      youtubeLink: "https://www.youtube.com/watch?v=KQetemT1sWc",
    };

    cy.addRecommendation(recommendation);
    cy.visit("/top");
    cy.contains(recommendation.name).should("be.visible");

    cy.contains("Random").click();
    cy.location("pathname").should("equal", "/random");
    cy.contains(recommendation.name).should("be.visible");
  });
});
