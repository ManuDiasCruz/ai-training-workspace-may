// Shared-instance deployment must never silently fall back to the public schema.
export function hostedDatabaseUrl(env) {
  const schema = env.DATABASE_SCHEMA;
  if (!/^singasong_[a-z0-9_]{1,54}$/.test(schema ?? "")) {
    throw new Error("DATABASE_SCHEMA must be a dedicated singasong_ schema (max 63 characters).");
  }
  let url;
  try {
    url = new URL(env.DATABASE_URL);
  } catch {
    throw new Error("A valid PostgreSQL DATABASE_URL is required.");
  }
  if (!["postgres:", "postgresql:"].includes(url.protocol) || !url.hostname || url.pathname.length < 2) {
    throw new Error("A valid PostgreSQL DATABASE_URL is required.");
  }
  url.searchParams.set("schema", schema);
  url.searchParams.set("connection_limit", "5");
  url.searchParams.set("connect_timeout", "15");
  return url.toString();
}
