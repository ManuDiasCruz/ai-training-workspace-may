describe("Sing Me A Song", () => {
  it("creates and votes on a recommendation through the deployed stack", () => {
    const name = `Smoke song ${Date.now()}`;

    cy.visit("/");
    cy.get('input[placeholder="Name"]').type(name);
    cy.get('input[placeholder="https://youtu.be/..."]').type(
      "https://youtu.be/dQw4w9WgXcQ"
    );

    cy.intercept("POST", "**/recommendations").as("createRecommendation");
    cy.get("button").click();
    cy.wait("@createRecommendation").its("response.statusCode").should("eq", 201);

    cy.contains(name)
      .parents("article")
      .within(() => {
        cy.get('[data-identifier="vote-menu"]').should("contain.text", "0");
        cy.get('[data-identifier="upvote"]').click();
      });

    cy.contains(name)
      .parents("article")
      .find('[data-identifier="vote-menu"]')
      .should("contain.text", "1");
  });
});
