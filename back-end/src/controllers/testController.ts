import { Request, Response } from "express";
import { testService } from "../services/testService.js";
import { wrongSchemaError } from "../utils/errorUtils.js";

export async function reset(req: Request, res: Response) {
  await testService.deleteData();

  res.sendStatus(200);
}

export async function seed(req: Request, res: Response) {
  const amount = Number(req.body?.amount ?? 10);
  const highScorePercentage = Number(req.body?.highScorePercentage ?? 0);

  if (!Number.isInteger(amount) || amount < 1 || amount > 1000) {
    throw wrongSchemaError("amount must be an integer between 1 and 1000");
  }
  if (
    !Number.isFinite(highScorePercentage) ||
    highScorePercentage < 0 ||
    highScorePercentage > 100
  ) {
    throw wrongSchemaError("highScorePercentage must be between 0 and 100");
  }

  const created = await testService.seedData(amount, highScorePercentage);

  res.status(201).send({ created });
}
