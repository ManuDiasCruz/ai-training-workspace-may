import supertest from "supertest";
import { jest } from "@jest/globals";

import app from "./../../src/app.js";
import { createRandomSong } from "../factories/recommendationFactory.js";
import { prisma } from "../../src/database.js";

const agent = supertest(app);

describe("INTEGRATION TESTS SUITE", () => {

    beforeAll(() => {
        if (process.env.NODE_ENV !== "test" || !new URL(process.env.DATABASE_URL).pathname.endsWith("_test")) {
            throw new Error("Integration tests require a dedicated _test database.");
        }
    });
    afterAll(async () => { await prisma.$disconnect(); });

    beforeEach(async () => {
        await prisma.$executeRaw`TRUNCATE TABLE recommendations RESTART IDENTITY`;
    });

    describe("POST /recommendations", () => {
        beforeEach(async () => {
            await prisma.recommendation.deleteMany({});
        });

        it("Create a recommendation", async () => {
            const song = createRandomSong();
        
            const response = await agent.post("/recommendations").send(song);
            expect(response.status).toBe(201);
        
            const { name, youtubeLink } = song;
            const checkUser = await prisma.recommendation.findFirst({
                where: { name, youtubeLink },
            });
        
            expect(checkUser).not.toBeNull();
        });
    
        it("Create a conflicting recommendation", async () => {
            const body = createRandomSong();
        
            const create = await agent.post("/recommendations").send(body);
            expect(create.status).toBe(201);
        
            const conflict = await agent.post("/recommendations").send(body);
            expect(conflict.status).toBe(409);
        });
    
        it("Create a 'invalid data' recommendation", async () => {
            const response = await agent.post("/recommendations").send({});
            expect(response.status).toBe(422);
        });
    });

    describe("GET /recommendations", () => {
        it("List recommendations", async () => {
            const recommendation1 = createRandomSong();
            const recommendation2 = createRandomSong();
            const recommendation3 = createRandomSong();
            
            await agent.post("/recommendations").send(recommendation1);
            await agent.post("/recommendations").send(recommendation2);
            await agent.post("/recommendations").send(recommendation3);
        
            const response = await agent.get("/recommendations");
            expect(response.status).toBe(200);
            expect(response.body).toHaveLength(3);
        
            expect(response.body[0].name).toBe(recommendation3.name);
            expect(response.body[0].youtubeLink).toBe(recommendation3.youtubeLink);
        
            expect(response.body[1].name).toBe(recommendation2.name);
            expect(response.body[1].youtubeLink).toBe(recommendation2.youtubeLink);

            expect(response.body[2].name).toBe(recommendation1.name);
            expect(response.body[2].youtubeLink).toBe(recommendation1.youtubeLink);
        });
    
        it("Show empty recommendations list", async () => {
            const response = await agent.get("/recommendations");
            expect(response.status).toBe(200);
            expect(response.body).toHaveLength(0);
        });
    
        it("List a random recommendation", async () => {
            const recommendation1 = createRandomSong();
            const recommendation2 = createRandomSong();
            const recommendation3 = createRandomSong();
        
            await agent.post("/recommendations").send(recommendation1);
            await agent.post("/recommendations").send(recommendation2);
            await agent.post("/recommendations").send(recommendation3);
        
            const response = await agent.get("/recommendations/random");
            expect(response.status).toBe(200);
            expect(response.body).toHaveProperty("name");
            expect(`${recommendation1.name} ${recommendation2.name} ${recommendation3.name}`).toContain(response.body.name);
        });
    
        it("List top recommendations", async () => {
            const recommendation1 = createRandomSong();
            const recommendation2 = createRandomSong();
            const recommendation3 = createRandomSong();
        
            const { body } = await agent.post("/recommendations").send(recommendation1);
            await agent.post("/recommendations").send(recommendation2);
            await agent.post("/recommendations").send(recommendation3);
        
            const vote = await agent.post(`/recommendations/${body.id}/upvote`);
            expect(vote.status).toBe(200);
        
            const response = await agent.get("/recommendations/top/2");
        
            expect(response.status).toBe(200);
            expect(response.body).toHaveLength(2);
        
            expect(response.body[0].name).toBe(recommendation1.name);
            expect(response.body[0].youtubeLink).toBe(recommendation1.youtubeLink);
        
            expect(response.body[1].name).toBe(recommendation2.name);
            expect(response.body[1].youtubeLink).toBe(recommendation2.youtubeLink);
        });
    
        it("Show a recommendation by id", async () => {
            const body = createRandomSong();
        
            await agent.post("/recommendations").send(body);
            
            const recommendation = await prisma.recommendation.findFirst({
                where: { name: body.name, youtubeLink: body.youtubeLink },
            });
        
            const response = await agent.get(`/recommendations/${recommendation.id}`);
        
            expect(response.status).toBe(200);
            expect(response.body.name).toBe(recommendation.name);
            expect(response.body.youtubeLink).toBe(recommendation.youtubeLink);
        });
    });
    
    describe("POST /upvote and /downvote", () => {
        it("Upvote a recommendation", async () => {
            const body = createRandomSong();
            await agent.post("/recommendations").send(body);
        
            const recommendation = await prisma.recommendation.findFirst({
                where: { name: body.name, youtubeLink: body.youtubeLink },
            });
        
            await agent.post(`/recommendations/${recommendation.id}/upvote`);
        
            await agent.post(`/recommendations/${recommendation.id}/upvote`);
        
            const response = await agent.get(`/recommendations/${recommendation.id}`);
        
            expect(response.status).toBe(200);
            expect(response.body.score).toBe(2);
        });
    
        it("Upvote non-existent recommendation", async () => {
            const response = await agent.post("/recommendations/1/upvote");
            expect(response.status).toBe(404);
        });
    
        it("Downvote a recommendation", async () => {
            const body = createRandomSong();
        
            await agent.post("/recommendations").send(body);
        
            const recommendation = await prisma.recommendation.findFirst({
                where: { name: body.name, youtubeLink: body.youtubeLink },
            });
        
            await agent.post(`/recommendations/${recommendation.id}/upvote`);
            await agent.post(`/recommendations/${recommendation.id}/upvote`);
            await agent.post(`/recommendations/${recommendation.id}/downvote`);
        
            const response = await agent.get(`/recommendations/${recommendation.id}`);
        
            expect(response.status).toBe(200);
            expect(response.body.score).toBe(1);
        });
    
        it("Downvote non-existent recommendation", async () => {
            const response = await agent.post("/recommendations/1/downvote");
            expect(response.status).toBe(404);
        });
    });
    describe("Regression coverage", () => {
        it.each(["abc", "0", "-1", "1.2", "2147483648"])("rejects invalid id %s", async id => {
            expect((await agent.get(`/recommendations/${id}`)).status).toBe(422);
            expect((await agent.post(`/recommendations/${id}/upvote`)).status).toBe(422);
            expect((await agent.post(`/recommendations/${id}/downvote`)).status).toBe(422);
        });
        it.each(["abc", "0", "-1", "1.5", "101"])("rejects invalid top amount %s", async amount => {
            expect((await agent.get(`/recommendations/top/${amount}`)).status).toBe(422);
        });
        it.each(["https://example.com/watch?v=qmUQr3zrqXM", "https://youtube.com/", "https://youtu.be/short", "javascript:alert(1)"])("rejects invalid video URL %s", async youtubeLink => {
            expect((await agent.post('/recommendations').send({ name: 'Invalid', youtubeLink })).status).toBe(422);
        });
        it("trims valid input and rejects blank names and additional fields", async () => {
            const song = createRandomSong();
            const created = await agent.post('/recommendations').send({ ...song, name: `  ${song.name}  ` });
            expect(created.body).toMatchObject({ name: song.name, score: 0 });
            expect((await agent.post('/recommendations').send({ ...song, name: '   ' })).status).toBe(422);
            expect((await agent.post('/recommendations').send({ ...song, score: 99 })).status).toBe(422);
        });
        it("returns 400 for malformed JSON and 413 for oversized bodies", async () => {
            expect((await agent.post('/recommendations').set('Content-Type', 'application/json').send('{')).status).toBe(400);
            expect((await agent.post('/recommendations').send({ name: 'a'.repeat(17000) })).status).toBe(413);
        });
        it("handles duplicate concurrent creates without a server error", async () => {
            const song = createRandomSong();
            const responses = await Promise.all([agent.post('/recommendations').send(song), agent.post('/recommendations').send(song)]);
            expect(responses.map(res => res.status).sort()).toEqual([201, 409]);
        });
        it("removes a recommendation on the sixth downvote", async () => {
            const created = await agent.post('/recommendations').send(createRandomSong());
            for (let i = 0; i < 6; i++) expect((await agent.post(`/recommendations/${created.body.id}/downvote`)).status).toBe(200);
            expect((await agent.get(`/recommendations/${created.body.id}`)).status).toBe(404);
            expect((await agent.get('/recommendations/random')).status).toBe(404);
        });
        it("limits the timeline but keeps older songs eligible for random selection", async () => {
            for (let i = 0; i < 12; i++) await agent.post('/recommendations').send(createRandomSong());
            const timeline = await agent.get('/recommendations');
            expect(timeline.body).toHaveLength(10);
            expect(timeline.body.map(song => song.id)).toEqual([12,11,10,9,8,7,6,5,4,3]);
            jest.spyOn(Math, 'random').mockReturnValue(0.99999);
            expect((await agent.get('/recommendations/random')).body.id).toBe(1);
        });
        it("reports healthy database access and keeps reset routes disabled", async () => {
            expect((await agent.get('/health')).body).toEqual({ status: 'ok' });
            expect((await agent.delete('/tests/reset')).status).toBe(404);
            expect((await agent.get('/recommendations/missing/route')).status).toBe(404);
        });
        it("allows the configured frontend origin but not unrelated origins", async () => {
            const allowed = await agent.options('/recommendations').set('Origin', 'http://localhost:3000').set('Access-Control-Request-Method', 'POST');
            expect(allowed.headers['access-control-allow-origin']).toBe('http://localhost:3000');
            const denied = await agent.options('/recommendations').set('Origin', 'https://untrusted.example').set('Access-Control-Request-Method', 'POST');
            expect(denied.headers['access-control-allow-origin']).toBeUndefined();
        });
    });
});

