import { Request, Response } from "express";
import { recommendationSchema } from "../schemas/recommendationsSchemas.js";
import { recommendationService } from "../services/recommendationsService.js";
import { wrongSchemaError } from "../utils/errorUtils.js";

async function insert(req: Request, res: Response) {
  const { error, value } = recommendationSchema.validate(req.body, {
    stripUnknown: true,
  });
  if (error) {
    throw wrongSchemaError(error.message);
  }

  await recommendationService.insert(value);

  res.sendStatus(201);
}

async function upvote(req: Request, res: Response) {
  const id = parsePositiveInteger(req.params.id, "id");

  await recommendationService.upvote(id);

  res.sendStatus(200);
}

async function downvote(req: Request, res: Response) {
  const id = parsePositiveInteger(req.params.id, "id");

  await recommendationService.downvote(id);

  res.sendStatus(200);
}

async function random(req: Request, res: Response) {
  const randomRecommendation = await recommendationService.getRandom();

  res.send(randomRecommendation);
}

async function get(req: Request, res: Response) {
  const recommendations = await recommendationService.get();
  res.send(recommendations);
}

async function getTop(req: Request, res: Response) {
  const amount = parsePositiveInteger(req.params.amount, "amount", 100);

  const recommendations = await recommendationService.getTop(amount);
  res.send(recommendations);
}

async function getById(req: Request, res: Response) {
  const id = parsePositiveInteger(req.params.id, "id");

  const recommendation = await recommendationService.getById(id);
  res.send(recommendation);
}

function parsePositiveInteger(value: string, field: string, max?: number) {
  const parsedValue = Number(value);
  if (
    !Number.isInteger(parsedValue) ||
    parsedValue <= 0 ||
    (max !== undefined && parsedValue > max)
  ) {
    const range = max ? ` between 1 and ${max}` : " a positive integer";
    throw wrongSchemaError(`${field} must be${range}`);
  }

  return parsedValue;
}

export const recommendationController = {
  insert,
  upvote,
  downvote,
  random,
  getTop,
  get,
  getById,
};
