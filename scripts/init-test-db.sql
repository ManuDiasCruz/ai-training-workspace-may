-- Runs once, the first time the docker-compose postgres volume is created.
-- The jest and Cypress suites reset this database, so it has to be separate
-- from the development one.
CREATE DATABASE singmeasong_test;
