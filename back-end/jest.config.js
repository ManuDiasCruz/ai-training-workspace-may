/** @type {import('ts-jest/dist/types').InitialOptionsTsJest} */
export default {
  // The plain "ts-jest" preset emits CommonJS, which breaks this package
  // ("type": "module"): the compiled test files referenced `exports` and
  // `import pkg from "@prisma/client"` resolved to undefined.
  preset: "ts-jest/presets/default-esm",
  testEnvironment: "node",
  extensionsToTreatAsEsm: [".ts"],
  globals: {
    "ts-jest": {
      useESM: true,
    },
  },
  // Source files import siblings with an explicit ".js" suffix (required by
  // Node's ESM resolver); strip it so jest resolves the ".ts" file.
  moduleNameMapper: {
    "^(\\.{1,2}/.*)\\.js$": "$1",
  },
};
