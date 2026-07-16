import "dotenv/config";
import { prisma } from "../src/database.js";

const recommendations = [
  {
    name: "Falamansa - Xote dos Milagres",
    youtubeLink: "https://www.youtube.com/watch?v=chwyjJbcs1Y",
    score: 12,
  },
  {
    name: "Legião Urbana - Tempo Perdido",
    youtubeLink: "https://www.youtube.com/watch?v=bdli16Bi8ik",
    score: 8,
  },
  {
    name: "Queen - Bohemian Rhapsody",
    youtubeLink: "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",
    score: 20,
  },
  {
    name: "a-ha - Take On Me",
    youtubeLink: "https://www.youtube.com/watch?v=djV11Xbc914",
    score: 5,
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
  .then(async () => {
    await prisma.$disconnect();
  })
  .catch(async (error) => {
    console.error(error);
    await prisma.$disconnect();
    process.exit(1);
  });
