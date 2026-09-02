import { hostedDatabaseUrl } from "../../scripts/hosted-database.mjs";

describe("shared-instance hosted database configuration", () => {
  const env = { DATABASE_URL: "postgresql://demo:example@localhost/app?sslmode=require&schema=public", DATABASE_SCHEMA: "singasong_0827_ben" };

  it("isolates migrations and runtime while retaining credentials, database and SSL options", () => {
    const url = new URL(hostedDatabaseUrl(env));
    expect(url.pathname).toBe("/app");
    expect(url.username).toBe("demo");
    expect(url.password).toBe("example");
    expect(url.searchParams.get("sslmode")).toBe("require");
    expect(url.searchParams.getAll("schema")).toEqual(["singasong_0827_ben"]);
    expect(url.searchParams.get("connection_limit")).toBe("5");
    expect(url.searchParams.get("connect_timeout")).toBe("15");
  });

  it.each([undefined, "public", "singasong_bad-name", "singasong_" + "a".repeat(55)])("rejects unsafe or missing schema %s", (schema) => {
    expect(() => hostedDatabaseUrl({ ...env, DATABASE_SCHEMA: schema })).toThrow("DATABASE_SCHEMA");
  });

  it.each([undefined, "invalid", "https://demo:example@localhost/app", "postgresql://localhost"])("rejects invalid database URLs without exposing them", (url) => {
    expect(() => hostedDatabaseUrl({ ...env, DATABASE_URL: url })).toThrow("A valid PostgreSQL DATABASE_URL is required.");
  });
});
