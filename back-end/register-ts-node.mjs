// Registers the ts-node ESM loader so the server can run TypeScript directly
// under Node 18+/22 (the deprecated --loader flag no longer works reliably).
import { register } from "node:module";
import { pathToFileURL } from "node:url";

register("ts-node/esm", pathToFileURL("./"));
