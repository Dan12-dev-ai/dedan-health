/// <reference types="vite/client" />

// Registers the `@testing-library/jest-dom` matcher types (`toBeInTheDocument`,
// `toHaveAttribute`, …) with TypeScript.
//
// The matchers work at runtime via `jest.setup.ts`, but without this reference
// `tsc --noEmit` rejects every DOM assertion with TS2339. The test suite
// therefore has to be *both* wired into Jest and typed for TypeScript.
import '@testing-library/jest-dom';

interface ImportMetaEnv {
  /** Base URL of the DEDAN v1 backend. Defaults to http://localhost:8000 */
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

