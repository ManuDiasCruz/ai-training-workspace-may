import "dotenv/config";
import app from "./app.js";
import { prisma } from "./database.js";

const PORT = process.env.PORT || 5000;
if (!process.env.DATABASE_URL) {
  throw new Error("DATABASE_URL is required. See back-end/.env.example.");
}

const server = app.listen(PORT, () => {
  console.log(`Server is listening on port ${PORT}.`);
});

function shutdown(signal: string) {
  console.log(`${signal} received; closing HTTP server.`);
  server.close(async () => {
    await prisma.$disconnect();
    process.exit(0);
  });
}

process.once("SIGTERM", () => shutdown("SIGTERM"));
process.once("SIGINT", () => shutdown("SIGINT"));
