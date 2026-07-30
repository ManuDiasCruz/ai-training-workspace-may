// Each test seeds its own data, so the table is wiped before every one of them.
// With a single `before` the second test inherited the first test's songs and
// its seeded names collided with the unique `name` column.
beforeEach(() => {
    cy.resetPosts();
});

describe("E2E tests: Render Screen", () => {
    it("Renders /random from a database with mostly high-scored songs", () => {
        // The original numbers (100 songs, then 50) meant well over a thousand
        // HTTP requests per run. These are large enough to exercise the score
        // filter without making the suite take minutes.
        const amount = 20;
        const highScorePercentage = 70;
        cy.seedDatabase(amount, highScorePercentage);

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

        cy.get('[data-identifier="recommendation"]').should("have.length", 1);
    });

    it("Renders /top with the ten highest scored songs", () => {
        const amount = 15;
        const highScorePercentage = 100;
        cy.seedDatabase(amount, highScorePercentage);

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

        cy.get('[data-identifier="recommendation"]').should("have.length", 10);
    });
});
