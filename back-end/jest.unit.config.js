import baseConfig from "./jest.config.js";

export default {
  ...baseConfig,
  moduleNameMapper: {
    "^\\.\\./database\\.js$": "<rootDir>/tests/mocks/database.ts",
    "^\\.\\./\\.\\./src/database\\.js$": "<rootDir>/tests/mocks/database.ts",
    ...baseConfig.moduleNameMapper,
  },
};
