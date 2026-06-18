import { Request, Response } from "express";
import { testService } from "../services/testService.js";

export async function reset(req: Request, res: Response) {
    await testService.deleteData();

    res.sendStatus(200);
}
