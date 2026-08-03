import { Request, Response } from "express";
import { seedSchema } from "../schemas/recommendationsSchemas.js";
import { testService } from "../services/testService.js";
import { wrongSchemaError } from "../utils/errorUtils.js";

export async function reset(req: Request, res: Response) {
    await testService.deleteData();

    res.sendStatus(200);
}

export async function seed(req: Request, res: Response) {
    const validation = seedSchema.validate(req.body);
    if (validation.error) {
        throw wrongSchemaError(validation.error.message);
    }

    const result = await testService.seedData(validation.value);

    res.status(201).send(result);
}
