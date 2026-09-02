import { faker } from "@faker-js/faker";

import * as setup from "./utils/setup.js";

beforeEach(() => {
    cy.resetPosts();
});

describe("E2E tests: POST /recommendations", () => {
    it("Add a song", () => {
        const {name, youtubeLink} = setup.createRecommendation();

        cy.visit("http://localhost:3000/");
        
        cy.get("input").first().type(name);
        cy.get("input").last().type(youtubeLink);

        cy.intercept("POST", "/recommendations").as("createRecommendation");
        cy.get("button").click();

        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(201);
        });      
    });

    it("Add a wrong link song", () => {
        const {name, youtubeLink} = setup.createWrongLink();

        cy.visit("http://localhost:3000/");
        cy.get("input").first().type(name);
        cy.get("input").last().type(youtubeLink);
    
        cy.intercept("POST", "/recommendations").as("createRecommendation");
        cy.get("button").click();

        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(422);
        });
    });

    it("Add a empty infos song", () => {
        cy.visit("http://localhost:3000/");
    
        cy.intercept("POST", "/recommendations").as("createRecommendation");
        cy.get("button").click();

        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(422);
        });
    });  

    it("Add a duplicated song", () => {
        const song = setup.createRecommendation();
  
        cy.addSong(song);
  
        cy.visit("http://localhost:3000/");
        cy.get("input").first().type(song.name);
        cy.get("input").last().type(song.youtubeLink);
  
        cy.intercept("POST", "/recommendations").as("createRecommendation");
        cy.get("button").click();
  
        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(409);
        });
    });
    
    it("Add >= 10 posts => Show only 10 posts", () => {
        cy.visit("http://localhost:3000/");
    
        for (let i = 0; i < 15; i++) {
            const {name, youtubeLink} = setup.createWrongLink();
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