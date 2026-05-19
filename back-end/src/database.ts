import * as PrismaPkg from "@prisma/client";

const pkgWithDefault = PrismaPkg as typeof PrismaPkg & { default?: typeof PrismaPkg };
const { PrismaClient } = pkgWithDefault.PrismaClient
  ? pkgWithDefault
  : (pkgWithDefault.default as typeof PrismaPkg);

export const prisma = new PrismaClient();
