import "dotenv/config";
import app from "./app.js";
import { prisma } from "./database.js";

const port = Number(process.env.PORT ?? 5000);
if (!Number.isInteger(port) || port < 1 || port > 65535) throw new Error("PORT must be 1-65535");
try {
  await prisma.$connect();
  const server = app.listen(port, "0.0.0.0", () => console.log(`Server is listening on port ${port}.`));
  const shutdown = () => {
    const timeout = setTimeout(() => process.exit(1), 10000);
    timeout.unref();
    server.close(async () => {
      await prisma.$disconnect();
      clearTimeout(timeout);
      process.exit(0);
    });
  };
  process.once("SIGTERM", shutdown);
  process.once("SIGINT", shutdown);
} catch {
  console.error("Database connection failed. Check DATABASE_URL and database availability.");
  await prisma.$disconnect();
  process.exit(1);
}
