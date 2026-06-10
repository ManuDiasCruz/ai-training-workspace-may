describe("Sing Me A Song smoke", () => {
  it("renders the app shell", () => {
    cy.visit("/");

    cy.contains("Sing me a Song").should("be.visible");
    cy.contains("Home").should("be.visible");
    cy.contains("Top").should("be.visible");
    cy.contains("Random").should("be.visible");
  });
});
