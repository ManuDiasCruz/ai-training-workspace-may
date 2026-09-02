/** @type {import('ts-jest/dist/types').InitialOptionsTsJest} */
export default {
  // The ESM preset is required. With the plain "ts-jest" preset the sources are
  // emitted as CommonJS while Node links them as ESM (package.json declares
  // "type": "module"), which fails with "ReferenceError: exports is not defined".
  preset: "ts-jest/presets/default-esm",
  testEnvironment: "node",
  extensionsToTreatAsEsm: [".ts"],
  globals: {
    "ts-jest": {
      useESM: true,
    },
  },
  // Lets ESM-style "./foo.js" specifiers resolve to the "./foo.ts" sources.
  // Both dots must stay escaped, otherwise the pattern also swallows the
  // ".mjs" chunks that @faker-js/faker imports internally.
  moduleNameMapper: {
    "^(\\.{1,2}/.*)\\.js$": "$1",
  },
};
