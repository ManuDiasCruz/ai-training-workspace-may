import pkg from "@prisma/client";

const { PrismaClient } = pkg;
const prisma = new PrismaClient();

const songs = [
  {
    name: "Queen - Bohemian Rhapsody",
    youtubeLink: "https://www.youtube.com/watch?v=fJ9rUzIMcZQ",
    score: 12,
  },
  {
    name: "Rick Astley - Never Gonna Give You Up",
    youtubeLink: "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
    score: 8,
  },
  {
    name: "Toto - Africa",
    youtubeLink: "https://www.youtube.com/watch?v=FTQbiNvZqaY",
    score: 5,
  },
  {
    name: "a-ha - Take On Me",
    youtubeLink: "https://www.youtube.com/watch?v=djV11Xbc914",
    score: 3,
  },
  {
    name: "Tim Maia - Não Quero Dinheiro",
    youtubeLink: "https://www.youtube.com/watch?v=RJmYEX9CDCs",
    score: 0,
  },
];

async function main() {
  for (const song of songs) {
    await prisma.recommendation.upsert({
      where: { name: song.name },
      update: {},
      create: song,
    });
  }

  console.log(`Seeded ${songs.length} recommendations.`);
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(() => prisma.$disconnect());
