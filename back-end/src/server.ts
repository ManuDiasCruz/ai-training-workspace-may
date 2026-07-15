import "dotenv/config";

import app from "./app.js";
import { prisma } from "./database.js";

const port = Number(process.env.PORT ?? 5000);

if (!Number.isInteger(port) || port <= 0) {
  throw new Error("PORT must be a positive integer");
}

const server = app.listen(port, () => {
  console.log(`Server is listening on port ${port}.`);
});

async function shutdown(signal: string) {
  console.log(`${signal} received. Shutting down gracefully.`);

  server.close(async () => {
    await prisma.$disconnect();
    process.exit(0);
  });
}

process.once("SIGINT", () => void shutdown("SIGINT"));
process.once("SIGTERM", () => void shutdown("SIGTERM"));
