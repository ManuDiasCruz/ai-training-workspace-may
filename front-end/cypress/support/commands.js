Cypress.Commands.add("resetData", () => {
    cy.request("DELETE", `${Cypress.env("apiUrl")}/tests/reset`);
});

//createPost
Cypress.Commands.add("addSong", (song) => {
    cy.request("POST", `${Cypress.env("apiUrl")}/recommendations`, song).then(
        (res) => cy.log(res)
    );
});
