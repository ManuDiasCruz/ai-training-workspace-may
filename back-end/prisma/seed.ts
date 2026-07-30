import "dotenv/config";

import { prisma } from "../src/database.js";

const recommendations = [
  {
    name: "Chitãozinho E Xororó - Evidências",
    youtubeLink: "https://www.youtube.com/watch?v=ePjtnSPFWK8",
    score: 12,
  },
  {
    name: "Rick Astley - Never Gonna Give You Up",
    youtubeLink: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    score: 8,
  },
  {
    name: "Falamansa - Xote dos Milagres",
    youtubeLink: "https://www.youtube.com/watch?v=chwyjJbcs1Y",
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
  .catch((error) => {
    console.error(error);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
