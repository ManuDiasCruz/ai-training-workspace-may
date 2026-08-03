import * as setup from "./utils/setup.js";

beforeEach(() => {
    cy.resetPosts();
});

describe("E2E tests: POST /recommendations", () => {
    it("Add a song", () => {
        const {name, youtubeLink} = setup.createRecommendation();

        cy.visit("/");

        cy.get('[data-identifier="name"]').type(name);
        cy.get('[data-identifier="link"]').type(youtubeLink);

        cy.intercept("POST", "**/recommendations").as("createRecommendation");
        cy.get('[data-identifier="create"]').click();

        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(201);
        });

        cy.contains(name).should("be.visible");
    });

    it("Add a wrong link song", () => {
        const {name, youtubeLink} = setup.createWrongLink();

        cy.visit("/");
        cy.get('[data-identifier="name"]').type(name);
        cy.get('[data-identifier="link"]').type(youtubeLink);

        cy.intercept("POST", "**/recommendations").as("createRecommendation");
        cy.get('[data-identifier="create"]').click();

        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(422);
        });
    });

    it("Add a empty infos song", () => {
        cy.visit("/");

        cy.intercept("POST", "**/recommendations").as("createRecommendation");
        cy.get('[data-identifier="create"]').click();

        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(422);
        });
    });

    it("Add a duplicated song", () => {
        const song = setup.createRecommendation();

        cy.addSong(song);

        cy.visit("/");
        cy.get('[data-identifier="name"]').type(song.name);
        cy.get('[data-identifier="link"]').type(song.youtubeLink);

        cy.intercept("POST", "**/recommendations").as("createRecommendation");
        cy.get('[data-identifier="create"]').click();

        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(409);
        });
    });

    // This used to build the 15 songs with setup.createWrongLink(), so every
    // POST answered 422, nothing was ever persisted, and the "at least one
    // card" assertion could not pass. GET /recommendations takes 10 rows max.
    it("Add >= 10 posts => Show only 10 posts", () => {
        const songs = Array.from({ length: 15 }, () => setup.createRecommendation());

        songs.forEach((song) => cy.addSong(song));

        cy.visit("/");

        cy.get('[data-identifier="vote-menu"]')
            .should("have.length.gte", 1)
            .and("have.length.lte", 10);

        cy.get('[data-identifier="vote-menu"]').should("have.length", 10);
    });
});
