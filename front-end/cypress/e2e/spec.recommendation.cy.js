/// <reference types="cypress" />

import { faker } from "@faker-js/faker";

function createRecommendation() {
  const name = "Mundo Bita - O Circo chegou";

  const youtubeLink = "https://www.youtube.com/watch?v=qmUQr3zrqXM";

  return { name, youtubeLink };
}

function createWrongLink() {
  const name = faker.name.findName();
  const youtubeLink = name;

  return { name, youtubeLink };
}

function createValidSong() {
  const name = `${faker.name.findName()} - ${faker.random.alphaNumeric(8)}`;
  const youtubeLink = `https://www.youtube.com/watch?v=${faker.random.alphaNumeric(11)}`;

  return { name, youtubeLink };
}

describe("E2E tests: POST /recommendations", () => {
    beforeEach(() => {
        cy.resetData();
    });

    it("Add a song", () => {
        const { name, youtubeLink } = createRecommendation();

        cy.visit("/");

        cy.get("input[placeholder='Name']").type(name);
        cy.get("input[placeholder='https://youtu.be/...']").type(youtubeLink);

        cy.intercept("POST", "/recommendations").as("createRecommendation");
        cy.get("button").click();

        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(201);
        });

        cy.contains(name).should("exist");
    });

    it("Add a wrong link song", () => {
        const {name, youtubeLink} = createWrongLink();

        cy.visit("/");
        cy.get("input").first().type(name);
        cy.get("input").last().type(youtubeLink);

        cy.intercept("POST", "/recommendations").as("createRecommendation");
        cy.get("button").click();

        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(422);
        });
    });

    it("Add a empty infos song", () => {
        cy.visit("/");

        cy.intercept("POST", "/recommendations").as("createRecommendation");
        cy.get("button").click();

        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(422);
        });
    });

    it("Add a duplicated song", () => {
        const song = createRecommendation();

        cy.addSong(song);

        cy.visit("/");
        cy.get("input").first().type(song.name);
        cy.get("input").last().type(song.youtubeLink);

        cy.intercept("POST", "/recommendations").as("createRecommendation");
        cy.get("button").click();

        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(409);
        });
    });

    it("Add >= 10 posts => Show only 10 posts", () => {
        cy.visit("/");

        for (let i = 0; i < 15; i++) {
            const {name, youtubeLink} = createValidSong();
            cy.get("input").first().type(name);
            cy.get("input").last().type(youtubeLink);

            cy.intercept("POST", "/recommendations").as("createRecommendation");
            cy.get("button").click();
            cy.wait("@createRecommendation");

            cy.get('[data-identifier="vote-menu"]')
                .should("have.length.gte", 1)
                .and("have.length.lte", 10);
        }
    });
});

describe("E2E tests: voting", () => {
    beforeEach(() => {
        cy.resetData();
        cy.addSong(createRecommendation());
    });

    it("Upvote a song", () => {
        cy.visit("/");

        cy.intercept("POST", "/recommendations/*/upvote").as("upvoteSong");
        cy.get('[data-identifier="upvote"]').click();
        cy.wait("@upvoteSong").then((res) => {
            expect(res.response.statusCode).to.equals(200);
        });

        cy.get('[data-identifier="score"]').should("have.text", "1");
    });

    it("Downvote a song", () => {
        cy.visit("/");

        cy.intercept("POST", "/recommendations/*/downvote").as("downvoteSong");
        cy.get('[data-identifier="downvote"]').click();
        cy.wait("@downvoteSong").then((res) => {
            expect(res.response.statusCode).to.equals(200);
        });

        cy.get('[data-identifier="score"]').should("have.text", "-1");
    });

    it("Downvote below -5 removes the recommendation", () => {
        const { name } = createRecommendation();

        cy.visit("/");

        cy.intercept("POST", "/recommendations/*/downvote").as("downvoteSong");

        for (let i = 1; i <= 5; i++) {
            cy.get('[data-identifier="downvote"]').click();
            cy.wait("@downvoteSong");
            // waiting for the refreshed score keeps the next click off a stale element
            cy.get('[data-identifier="score"]').should("have.text", `${-i}`);
        }

        cy.get('[data-identifier="downvote"]').click();
        cy.wait("@downvoteSong");

        cy.contains(name).should("not.exist");
        cy.contains("No recommendations yet! Create your own :)").should("exist");
    });
});

describe("E2E tests: render screens", () => {
    beforeEach(() => {
        cy.resetData();
        cy.addSong(createRecommendation());
    });

    it("Top page lists recommendations by score", () => {
        cy.intercept("GET", "/recommendations/top/10").as("getTopRecommendations");
        cy.visit("/top");

        cy.wait("@getTopRecommendations").then(({ response }) => {
            expect(response.statusCode).to.equals(200);
            expect(response.body[0]).to.haveOwnProperty("name");
            expect(response.body[0]).to.haveOwnProperty("youtubeLink");
            expect(response.body[0]).to.haveOwnProperty("score");
        });

        cy.get('[data-identifier="vote-menu"]').should("have.length", 1);
    });

    it("Random page shows a recommendation", () => {
        cy.intercept("GET", "/recommendations/random").as("getRandomRecommendation");
        cy.visit("/random");

        cy.wait("@getRandomRecommendation").then(({ response }) => {
            expect(response.statusCode).to.equals(200);
            expect(response.body).to.haveOwnProperty("name");
            expect(response.body).to.haveOwnProperty("youtubeLink");
            expect(response.body).to.haveOwnProperty("score");
        });

        cy.contains("Mundo Bita - O Circo chegou").should("exist");
    });
});
