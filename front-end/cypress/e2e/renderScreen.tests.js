beforeEach(() => {
    cy.resetPosts();
});

describe("E2E tests: Render Screen", () => {
    it("Renders a random recommendation", () => {
        const amount = 100;
        const highScorePercentage = 70;
        cy.seedDatabase(amount, highScorePercentage);

        cy.intercept("GET", "**/recommendations/random").as(
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

    it("Renders the 10 top recommendations, highest score first", () => {
        const amount = 50;
        const highScorePercentage = 100;
        cy.seedDatabase(amount, highScorePercentage);

        cy.intercept("GET", "**/recommendations/top/10").as("getTopRecommendations");
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

    it("Shows the empty state when there is nothing to recommend", () => {
        cy.visit("/");
        cy.get('[data-identifier="empty-state"]').should("be.visible");

        cy.visit("/random");
        cy.get('[data-identifier="empty-state"]').should("be.visible");
    });
});
