const apiUrl = () => Cypress.env("apiUrl") ?? "";

// Reset the database via the back-end test-only helper route.
// NOTE: the route is mounted at /tests/reset (the test router is mounted on
// "/tests"), and is only available when the back-end runs with MODE=TEST.
Cypress.Commands.add("resetData", () => {
    cy.request("DELETE", `${apiUrl()}/tests/reset`);
});

// Create a recommendation directly through the API.
Cypress.Commands.add("addSong", (song) => {
    cy.request("POST", `${apiUrl()}/recommendations`, song).then(
        (res) => cy.log(JSON.stringify(res.body))
    );
});
