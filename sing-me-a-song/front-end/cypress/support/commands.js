Cypress.Commands.add("resetData", () => {
    cy.request("DELETE", "http://localhost:5000/reset");
});

//createPost
Cypress.Commands.add("addSong", (song) => {
    cy.request("POST", "http://localhost:5000/recommendations", song).then(
        (res) => cy.log(res)
    );
});