/**
 * Jest configuration for the DEDAN Health web portal.
 *
 * Notes:
 *  - `babel-jest` compiles TS/TSX to CommonJS. The Babel presets are pinned to
 *    v7 to match `@babel/core` v7 (v8 presets are incompatible with it).
 *  - `src/services/apiClient.ts` reads `import.meta.env`, which Babel cannot
 *    lower to CommonJS. It is mapped to a stub with an identical public
 *    surface so tests can still exercise the real client behaviour.
 */
/** @type {import('jest').Config} */
module.exports = {
  testEnvironment: 'jsdom',
  roots: ['<rootDir>/src/__tests__'],
  testMatch: ['**/*.test.ts', '**/*.test.tsx'],
  transform: {
    '^.+\\.tsx?$': ['babel-jest', { configFile: './babel.config.cjs' }],
  },
  moduleNameMapper: {
    // Jest stub for the Vite `import.meta.env` accessor. Matches the
    // extension-less relative specifier used inside `src/services/*`.
    '^\\./apiClient$': '<rootDir>/src/__mocks__/apiClient.stub.ts',
    '^(.*)/services/apiClient$': '<rootDir>/src/__mocks__/apiClient.stub.ts',
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
  },
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  collectCoverageFrom: ['src/**/*.{ts,tsx}', '!src/**/*.d.ts', '!src/__mocks__/**'],
};
