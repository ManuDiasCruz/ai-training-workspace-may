import { Request, Response } from "express";
import { recommendationSchema } from "../schemas/recommendationsSchemas.js";
import { recommendationService } from "../services/recommendationsService.js";
import { wrongSchemaError } from "../utils/errorUtils.js";

async function insert(req: Request, res: Response) {
  const validation = recommendationSchema.validate(req.body);
  if (validation.error) {
    throw wrongSchemaError();
  }

  const recommendation = await recommendationService.insert(req.body);

  res.status(201).json(recommendation);
}

async function upvote(req: Request, res: Response) {
  await recommendationService.upvote(parsePositiveInteger(req.params.id, "id"));

  res.sendStatus(200);
}

async function downvote(req: Request, res: Response) {
  await recommendationService.downvote(parsePositiveInteger(req.params.id, "id"));

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
  const amount = parsePositiveInteger(req.params.amount, "amount");
  const recommendations = await recommendationService.getTop(amount);
  res.send(recommendations);
}

async function getById(req: Request, res: Response) {
  const recommendation = await recommendationService.getById(
    parsePositiveInteger(req.params.id, "id")
  );
  res.send(recommendation);
}

function parsePositiveInteger(value: string, field: string) {
  const number = Number(value);

  if (!Number.isSafeInteger(number) || number < 1) {
    throw wrongSchemaError(`${field} must be a positive integer`);
  }

  return number;
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
