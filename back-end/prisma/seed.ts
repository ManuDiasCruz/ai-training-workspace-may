import "dotenv/config";

import { prisma } from "../src/database.js";

const recommendations = [
  {
    name: "Chitãozinho & Xororó - Evidências",
    youtubeLink: "https://www.youtube.com/watch?v=ZzqbCFRSbtc",
    score: 42,
  },
  {
    name: "Queen - Bohemian Rhapsody",
    youtubeLink: "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",
    score: 31,
  },
  {
    name: "Falamansa - Xote dos Milagres",
    youtubeLink: "https://www.youtube.com/watch?v=chwyjJbcs1Y",
    score: 15,
  },
  {
    name: "a-ha - Take On Me",
    youtubeLink: "https://www.youtube.com/watch?v=djV11Xbc914",
    score: 8,
  },
  {
    name: "Rick Astley - Never Gonna Give You Up",
    youtubeLink: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    score: 3,
  },
];

async function main() {
  for (const recommendation of recommendations) {
    await prisma.recommendation.upsert({
      where: { name: recommendation.name },
      update: {},
      create: recommendation,
    });
  }

  console.log(`Seeded ${recommendations.length} recommendations.`);
}

main()
  .catch((error) => {
    console.error(error);
    process.exitCode = 1;
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
