/// <reference types="cypress" />

import { faker } from "@faker-js/faker";

async function createRecommendation() {
  const name = "Mundo Bita - O Circo chegou";

  const youtubeLink = "https://www.youtube.com/watch?v=qmUQr3zrqXM";    

  return { name, youtubeLink };
}

function createWrongLink() {
  const name = faker.name.findName();
  const youtubeLink = name;    

  return { name, youtubeLink };
}



describe("E2E tests: POST /recommendations", () => {
    beforeEach(() => {
        cy.resetData();
    });

    it("Add a song", () => {
        const song = createRecommendation();

        cy.visit("http://localhost:3000/");
        
        cy.get("input[placeholder='Name']").type(name);
        cy.get("input[placeholder='https://youtu.be/...']").type(youtubeLink);

        cy.intercept("POST", "/recommendations").as("createRecommendation");
        cy.get("button").click();

        cy.wait("@createRecommendation").then((res) => {
            expect(res.response.statusCode).to.equals(201);
        });      
    });

    it("Add a wrong link song", () => {
        const {name, youtubeLink} = createWrongLink();

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
        const song = createRecommendation();
  
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
            const {name, youtubeLink} = createWrongLink();
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