export function assertTestDatabase() {
  let databaseName = "";
  try {
    databaseName = new URL(process.env.DATABASE_URL ?? "").pathname.slice(1);
  } catch { /* Reject missing/malformed URLs without exposing credentials. */ }
  if (process.env.NODE_ENV !== "test" || !databaseName.endsWith("_test")) {
    throw new Error("Destructive tests require NODE_ENV=test and a database name ending in _test");
  }
}
