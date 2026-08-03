export const recommendationSchema = `
  CREATE TABLE IF NOT EXISTS recommendations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    youtubeLink TEXT NOT NULL,
    score INTEGER NOT NULL DEFAULT 0
  )
`;
