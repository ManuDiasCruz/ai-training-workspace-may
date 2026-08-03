import { Request, Response } from "express";
import { recommendationSchema } from "../schemas/recommendationsSchemas.js";
import { recommendationService } from "../services/recommendationsService.js";
import { wrongSchemaError } from "../utils/errorUtils.js";

// `+id` on a non-numeric route param yields NaN, which Prisma rejects with an
// opaque error that the error handler turns into a 500. Validating here keeps
// bad input in the 4xx range where it belongs.
function parsePositiveInt(raw: string, field: string) {
  const parsed = Number(raw);

  if (!Number.isInteger(parsed) || parsed < 1) {
    throw wrongSchemaError(`"${field}" must be a positive integer`);
  }

  return parsed;
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
  const { id } = req.params;

  await recommendationService.upvote(parsePositiveInt(id, "id"));

  res.sendStatus(200);
}

async function downvote(req: Request, res: Response) {
  const { id } = req.params;

  await recommendationService.downvote(parsePositiveInt(id, "id"));

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
  const { amount } = req.params;

  const recommendations = await recommendationService.getTop(
    parsePositiveInt(amount, "amount")
  );
  res.send(recommendations);
}

async function getById(req: Request, res: Response) {
  const { id } = req.params;

  const recommendation = await recommendationService.getById(
    parsePositiveInt(id, "id")
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
