describe("E2E tests: Render Screen", () => {
    beforeEach(() => {
        cy.resetPosts();
    });

    it("Renders a random recommendation", () => {
        cy.seedDatabase(100, 70);

        cy.intercept("GET", "/recommendations/random").as(
            "getRandomRecommendation"
        );

        cy.visit("/random");

        cy.wait("@getRandomRecommendation").then(({ response }) => {
            expect(response.statusCode).to.equal(200);
            expect(response.body).to.haveOwnProperty("name");
            expect(response.body).to.haveOwnProperty("youtubeLink");
            expect(response.body).to.haveOwnProperty("score");
        });

        cy.get('[data-identifier="vote-menu"]').should("have.length", 1);
    });

    it("Renders the top 10 recommendations ordered by score", () => {
        cy.seedDatabase(50, 100);

        cy.intercept("GET", "/recommendations/top/10").as("getTopRecommendations");
        cy.visit("/top");

        cy.wait("@getTopRecommendations").then(({ response }) => {
            expect(response.statusCode).to.equal(200);
            expect(response.body.length).to.equal(10);
            expect(response.body[0]).to.haveOwnProperty("name");
            expect(response.body[0]).to.haveOwnProperty("youtubeLink");
            expect(response.body[0]).to.haveOwnProperty("score");
            expect(response.body[0].score).to.gte(response.body[9].score);
        });

        cy.get('[data-identifier="vote-menu"]').should("have.length", 10);
    });

    it("Renders the home timeline with at most 10 recommendations", () => {
        cy.seedDatabase(25, 50);

        cy.intercept("GET", "/recommendations").as("getRecommendations");
        cy.visit("/");

        cy.wait("@getRecommendations").then(({ response }) => {
            expect(response.statusCode).to.equal(200);
            expect(response.body.length).to.equal(10);
        });

        cy.get('[data-identifier="vote-menu"]').should("have.length", 10);
    });
});
