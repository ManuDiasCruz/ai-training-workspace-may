/// <reference types="cypress" />

import * as setup from "./utils/setup.js";

beforeEach(() => {
  cy.resetPosts();
});

describe("E2E tests: POST /recommendations", () => {
  it("Add a song", () => {
    const { name, youtubeLink } = setup.createRecommendation();

    cy.visit("/");

    cy.get("input").first().type(name);
    cy.get("input").last().type(youtubeLink);

    cy.intercept("POST", "/recommendations").as("createRecommendation");
    cy.get("button").click();

    cy.wait("@createRecommendation").then((res) => {
      expect(res.response.statusCode).to.equals(201);
    });

    cy.contains(name).should("exist");
  });

  it("Add a wrong link song", () => {
    const { name, youtubeLink } = setup.createWrongLink();

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
    const song = setup.createRecommendation();

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

    for (let i = 0; i < 12; i++) {
      const { name, youtubeLink } = setup.createRandomSong();
      cy.get("input").first().type(name);
      cy.get("input").last().type(youtubeLink);

      cy.intercept("POST", "/recommendations").as("createRecommendation");
      cy.intercept("GET", "/recommendations").as("listRecommendations");
      cy.get("button").click();
      cy.wait("@createRecommendation");
      cy.wait("@listRecommendations");

      cy.get('[data-identifier="vote-menu"]')
        .should("have.length.gte", 1)
        .and("have.length.lte", 10);
    }
  });
});
