import { Request, Response } from "express";
import { recommendationSchema } from "../schemas/recommendationsSchemas.js";
import { recommendationService } from "../services/recommendationsService.js";
import { notFoundError, wrongSchemaError } from "../utils/errorUtils.js";

function parseIdOrFail(id: string) {
  const parsedId = Number(id);
  if (!Number.isInteger(parsedId)) throw notFoundError();

  return parsedId;
}

async function insert(req: Request, res: Response) {
  const validation = recommendationSchema.validate(req.body);
  if (validation.error) {
    throw wrongSchemaError();
  }

  await recommendationService.insert(req.body);

  res.sendStatus(201);
}

async function upvote(req: Request, res: Response) {
  const id = parseIdOrFail(req.params.id);

  await recommendationService.upvote(id);

  res.sendStatus(200);
}

async function downvote(req: Request, res: Response) {
  const id = parseIdOrFail(req.params.id);

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
  const amount = Number(req.params.amount);
  if (!Number.isInteger(amount) || amount < 1) {
    throw wrongSchemaError("amount must be a positive integer");
  }

  const recommendations = await recommendationService.getTop(amount);
  res.send(recommendations);
}

async function getById(req: Request, res: Response) {
  const id = parseIdOrFail(req.params.id);

  const recommendation = await recommendationService.getById(id);
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
