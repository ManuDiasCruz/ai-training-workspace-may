
import { Router } from "express";
import { reset, seed } from "../controllers/testController.js";

const testRouter = Router();

testRouter.delete("/reset", reset);
testRouter.post("/seed", seed);

export default testRouter;