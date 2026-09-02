import { Request, Response } from "express";
import { testService } from "../services/testService.js";
import { wrongSchemaError } from "../utils/errorUtils.js";

export async function reset(req: Request, res: Response) {
    await testService.deleteData();

    res.sendStatus(200);
}

export async function seed(req: Request, res: Response) {
    const { amount = 10, highScorePercentage = 50 } = req.body ?? {};

    const parsedAmount = Number(amount);
    const parsedPercentage = Number(highScorePercentage);

    if (!Number.isInteger(parsedAmount) || parsedAmount < 1 || parsedAmount > 500) {
        throw wrongSchemaError("amount must be an integer between 1 and 500");
    }

    if (!Number.isFinite(parsedPercentage) || parsedPercentage < 0 || parsedPercentage > 100) {
        throw wrongSchemaError("highScorePercentage must be between 0 and 100");
    }

    await testService.seed(parsedAmount, parsedPercentage);

    res.sendStatus(201);
}
