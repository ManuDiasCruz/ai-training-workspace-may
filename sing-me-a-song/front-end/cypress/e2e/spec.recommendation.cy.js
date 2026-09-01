/// <reference types="cypress" />
const song = { name: 'Mundo Bita - O Circo chegou', youtubeLink: 'https://www.youtube.com/watch?v=qmUQr3zrqXM' };

describe('Recommendation flows', () => {
  beforeEach(() => cy.resetData());

  it('creates, votes, and navigates through top and random', () => {
    cy.visit('/');
    cy.get('[aria-label="Song name"]').type(song.name);
    cy.get('[aria-label="YouTube link"]').type(song.youtubeLink);
    cy.get('[aria-label="Add recommendation"]').click();
    cy.contains('article', song.name).should('be.visible');
    cy.get('[data-identifier="upvote"]').click();
    cy.get('[aria-label="Score"]').should('have.text', '1');
    cy.contains('button', 'Top').click();
    cy.location('pathname').should('eq', '/top');
    cy.contains('article', song.name).should('be.visible');
    cy.contains('button', 'Random').click();
    cy.location('pathname').should('eq', '/random');
    cy.contains('article', song.name).should('be.visible');
  });

  it('preserves input after validation and duplicate errors', () => {
    cy.addSong(song);
    cy.visit('/');
    cy.get('[aria-label="Song name"]').type(song.name);
    cy.get('[aria-label="YouTube link"]').type('not-a-video');
    cy.get('[aria-label="Add recommendation"]').click();
    cy.get('[role="alert"]').should('contain', 'valid YouTube');
    cy.get('[aria-label="Song name"]').should('have.value', song.name);
    cy.get('[aria-label="YouTube link"]').clear().type(song.youtubeLink);
    cy.get('[aria-label="Add recommendation"]').click();
    cy.get('[role="alert"]').should('contain', 'already exists');
  });

  it('handles empty random results and deletion at minus six', () => {
    cy.visit('/random');
    cy.contains('No recommendations yet').should('be.visible');
    cy.addSong(song);
    cy.reload();
    for (let score = 0; score >= -5; score--) {
      cy.get('[aria-label="Score"]').should('have.text', String(score));
      cy.get('[data-identifier="downvote"]').click();
    }
    cy.contains('No recommendations yet').should('be.visible');
    cy.get('article').should('not.exist');
  });

  it('shows an API outage and recovers on retry', () => {
    cy.intercept({ method: 'GET', url: '**/recommendations', times: 1 }, { statusCode: 503, body: 'Unavailable' });
    cy.visit('/');
    cy.get('[role="alert"]').should('contain', 'Could not load recommendations');
    cy.contains('button', 'Retry').click();
    cy.contains('No recommendations yet').should('be.visible');
  });
});
