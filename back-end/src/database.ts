import pkg from "@prisma/client";

const { PrismaClient } = pkg;
type PrismaClientInstance = InstanceType<typeof PrismaClient>;

let client: PrismaClientInstance | undefined;

function getClient() {
  client ??= new PrismaClient();
  return client;
}

export const prisma = new Proxy({} as PrismaClientInstance, {
  get(_target, property) {
    const activeClient = getClient();
    const value = activeClient[property as keyof PrismaClientInstance];

    return typeof value === "function" ? value.bind(activeClient) : value;
  },
});

export async function disconnectPrisma() {
  await client?.$disconnect();
}
