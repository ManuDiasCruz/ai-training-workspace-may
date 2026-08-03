import dotenv from "dotenv";

// Loaded as the very first import of the process so that every module that
// reads `process.env` at import time (app.ts reads MODE, server.ts reads PORT)
// sees the values from the env file. When the process is already started
// through `dotenv-cli` (test scripts) the variables are simply left untouched,
// because dotenv never overwrites variables that are already defined.
const path = process.env.DOTENV_CONFIG_PATH ?? ".env";

dotenv.config({ path });

export {};
