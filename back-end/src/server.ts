import app from "./app.js";
import { prisma } from "./database.js";

const PORT = process.env.PORT || 5000;

if (!process.env.DATABASE_URL) {
  throw new Error(
    "DATABASE_URL is required. Copy .env.example to .env and configure PostgreSQL."
  );
}

const server = app.listen(PORT, () => {
  console.log(`Server is listening on port ${PORT}.`);
});

async function shutdown(signal: string) {
  console.log(`${signal} received. Closing the server.`);
  server.close(async () => {
    await prisma.$disconnect();
    process.exit(0);
  });
}

process.on("SIGTERM", () => shutdown("SIGTERM"));
process.on("SIGINT", () => shutdown("SIGINT"));
