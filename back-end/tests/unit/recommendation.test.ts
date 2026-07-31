import { jest } from "@jest/globals";
import { response } from "express";

import { recommendationService } from "../../src/services/recommendationsService.js";
import { recommendationRepository } from "../../src/repositories/recommendationRepository.js";
import { createRandomSong } from "../factories/recommendationFactory.js";

describe("UNIT TESTS SUITE", () => {

    const recommendation1 = createRandomSong();

    const recommendation2 = {
        id: 1,
        name: recommendation1.name,
        youtubeLink: recommendation1.youtubeLink,
        score: 2
    }

    describe("Create recommendation", () => {
        it("Success", async () => {
            const { name } = recommendation1;

            jest
                .spyOn(recommendationRepository, "findByName")
                .mockResolvedValueOnce(null);

            jest
                .spyOn(recommendationRepository, "create")
                .mockResolvedValueOnce(null);

            await recommendationService.insert(recommendation1);
            expect(recommendationRepository.findByName).toHaveBeenCalledWith(name);
            expect(recommendationRepository.create).toHaveBeenCalledTimes(1);
        });

        it("Fail", async () => {
            jest
                .spyOn(recommendationRepository, "findByName")
                .mockResolvedValueOnce(recommendation2);

            expect(recommendationService.insert(recommendation1)).rejects.toEqual(
                { message: "Recommendations names must be unique", type: "conflict" }
            );
        });
    });

    describe("Upvotes tests", () => {
        it("Sucess in upvote", async () => {
            jest
                .spyOn(recommendationRepository, "find")
                .mockResolvedValueOnce(recommendation2);
        
            jest
                .spyOn(recommendationRepository, "updateScore")
                .mockResolvedValueOnce(recommendation2);
            
            await recommendationService.upvote(1);
            expect(recommendationRepository.find).toHaveBeenCalledWith(1);
            expect(recommendationRepository.updateScore).toHaveBeenLastCalledWith(1, "increment"); 
        });

        it("Fail", async () => {
            jest
                .spyOn(recommendationRepository, "find")
                .mockResolvedValueOnce(null);
        
            expect(recommendationService.upvote(1)).rejects.toEqual(
                { message: "", type: "not_found" }
            );
        });
    });

    describe("Downvotes tests", () => {
        it("Success", async () => {
            jest
                .spyOn(recommendationRepository, "find")
                .mockResolvedValueOnce(recommendation2);
        
            jest
                .spyOn(recommendationRepository, "updateScore")
                .mockResolvedValueOnce(recommendation2);
            
            await recommendationService.downvote(1);
            expect(recommendationRepository.find).toHaveBeenCalledWith(1);
            expect(recommendationRepository.updateScore).toHaveBeenLastCalledWith(1, "decrement");   
        });

        it("Downvote deleting recommendation", async () => {
            jest
                .spyOn(recommendationRepository, "find")
                .mockResolvedValueOnce(recommendation2);
        
            jest
                .spyOn(recommendationRepository, "updateScore")
                .mockResolvedValueOnce({ ...recommendation2, score: -6 });

            jest
                .spyOn(recommendationRepository, "remove")
                .mockResolvedValueOnce(null);
            
            await recommendationService.downvote(1);
            expect(recommendationRepository.find).toHaveBeenCalledWith(1);
            expect(recommendationRepository.updateScore).toHaveBeenLastCalledWith(1, "decrement");
            expect(recommendationRepository.remove).toHaveBeenCalledTimes(1);
        });

        it("Fail", async () => {
            jest
                .spyOn(recommendationRepository, "find")
                .mockResolvedValueOnce(null);
        
            expect(recommendationService.downvote(1)).rejects.toEqual(
                { message: "", type: "not_found" }
            );
        });
    });

    describe("/GET tests", () => {
        it("Sucess in getByIdOrFail", async () => {
            jest
                .spyOn(recommendationRepository, "find")
                .mockResolvedValueOnce(recommendation2);

            const searched = await recommendationService.getById(1);
            expect(recommendationRepository.find).toHaveBeenCalledWith(1);
            expect(searched).toEqual(recommendation2);
        });

        it("Fail in getById", async () => {
            jest
                .spyOn(recommendationRepository, "find")
                .mockResolvedValueOnce(null);

            expect(recommendationService.getById(1)).rejects.toEqual({
                message: "",
                type: "not_found",
            });
        });

        it("Sucess", async () => {
            jest
                .spyOn(recommendationRepository, "findAll")
                .mockResolvedValueOnce([recommendation2]);

            const searched = await recommendationService.get();
            expect(recommendationRepository.findAll).toHaveBeenCalledTimes(1);
            expect(searched).toEqual([recommendation2]);
        });

        it("Sucess in getTop", async () => {
            jest
                .spyOn(recommendationRepository, "getAmountByScore")
                .mockResolvedValueOnce([recommendation2]);

            const searched = await recommendationService.getTop(1);
            expect(recommendationRepository.getAmountByScore).toHaveBeenCalledWith(1);
            expect(searched).toEqual([recommendation2]);
        });
    });

    describe("Random recommendations tests", () => {
        it("Success in get random gt", async () => {
            jest.spyOn(Math, "random").mockReturnValueOnce(0.5);

            jest
                .spyOn(recommendationRepository, "findAll")
                .mockResolvedValueOnce([recommendation2]);

            await recommendationService.getRandom();
            expect(recommendationRepository.findAll).toHaveBeenLastCalledWith({
                score: 10,
                scoreFilter: "gt",
            });
        });

        it("Success in get random lte", async () => {
            jest.spyOn(Math, "random").mockReturnValueOnce(0.8);

            jest
                .spyOn(recommendationRepository, "findAll")
                .mockResolvedValueOnce([recommendation2]);

            await recommendationService.getRandom();
            expect(recommendationRepository.findAll).toHaveBeenLastCalledWith({
                score: 10,
                scoreFilter: "lte",
            });
        });

        it("Error notfound in get random", async () => {
            jest.spyOn(Math, "random").mockReturnValueOnce(0.5);

            jest
                .spyOn(recommendationRepository, "findAll")
                .mockResolvedValueOnce([]);

            expect(recommendationService.getRandom()).rejects.toEqual({
                message: "",
                type: "not_found",
            });
        });
    });

});