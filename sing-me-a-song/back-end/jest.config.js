export default {
  testEnvironment: "node",
  extensionsToTreatAsEsm: [".ts"],
  transform: { "^.+\\.tsx?$": ["ts-jest", { useESM: true, tsconfig: {module:"ESNext", moduleResolution:"node"} }] },
  moduleNameMapper: { "^(\\.{1,2}/.*)\\.js$": "$1" },
  restoreMocks: true,
};
