import { Request, Response } from "express";
import { recommendationSchema } from "../schemas/recommendationsSchemas.js";
import { recommendationService } from "../services/recommendationsService.js";
import { wrongSchemaError } from "../utils/errorUtils.js";

async function insert(req: Request, res: Response) {
  const validation = recommendationSchema.validate(req.body);
  if (validation.error) {
    throw wrongSchemaError(validation.error.message);
  }

  const recommendation = await recommendationService.insert(validation.value);

  res.status(201).send(recommendation);
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

function parsePositiveInteger(value: string, name: string, maximum?: number) {
  const parsedValue = Number(value);
  const isOutOfRange = maximum !== undefined && parsedValue > maximum;

  if (!Number.isInteger(parsedValue) || parsedValue <= 0 || isOutOfRange) {
    const range = maximum ? ` between 1 and ${maximum}` : " greater than 0";
    throw wrongSchemaError(`${name} must be an integer${range}`);
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
