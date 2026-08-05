import "dotenv/config";
import app from "./app.js";
import { prisma } from "./database.js";

const PORT = Number(process.env.PORT) || 5000;
const server = app.listen(PORT, () => {
  console.log(`Server is listening on port ${PORT}.`);
});

async function shutdown(signal: string) {
  console.log(`${signal} received; closing server.`);
  server.close(async () => {
    await prisma.$disconnect();
    process.exit(0);
  });
}

process.once("SIGTERM", () => void shutdown("SIGTERM"));
process.once("SIGINT", () => void shutdown("SIGINT"));
