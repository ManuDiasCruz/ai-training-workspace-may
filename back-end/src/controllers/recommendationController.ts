import { Request, Response } from "express";
import { recommendationSchema } from "../schemas/recommendationsSchemas.js";
import { recommendationService } from "../services/recommendationsService.js";
import { wrongSchemaError } from "../utils/errorUtils.js";

function parsePositiveInteger(value: string) {
  const parsedValue = Number(value);

  if (!Number.isInteger(parsedValue) || parsedValue < 1) {
    throw wrongSchemaError("Route parameters must be positive integers");
  }

  return parsedValue;
}

async function insert(req: Request, res: Response) {
  const validation = recommendationSchema.validate(req.body, {
    abortEarly: false,
  });
  if (validation.error) {
    throw wrongSchemaError(validation.error.message);
  }

  const recommendation = await recommendationService.insert(validation.value);

  res.status(201).send(recommendation);
}

async function upvote(req: Request, res: Response) {
  const { id } = req.params;

  await recommendationService.upvote(parsePositiveInteger(id));

  res.sendStatus(200);
}

async function downvote(req: Request, res: Response) {
  const { id } = req.params;

  await recommendationService.downvote(parsePositiveInteger(id));

  res.sendStatus(200);
}

async function random(_req: Request, res: Response) {
  const randomRecommendation = await recommendationService.getRandom();

  res.send(randomRecommendation);
}

async function get(_req: Request, res: Response) {
  const recommendations = await recommendationService.get();
  res.send(recommendations);
}

async function getTop(req: Request, res: Response) {
  const { amount } = req.params;

  const recommendations = await recommendationService.getTop(
    parsePositiveInteger(amount)
  );
  res.send(recommendations);
}

async function getById(req: Request, res: Response) {
  const { id } = req.params;

  const recommendation = await recommendationService.getById(
    parsePositiveInteger(id)
  );
  res.send(recommendation);
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
