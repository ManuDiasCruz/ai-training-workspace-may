-- Runs once, the first time the postgres container initialises its data
-- directory. Creates the second database used by `npm test` and the Cypress
-- suite so that automated runs never touch development data.
CREATE DATABASE singmeasong_test;
