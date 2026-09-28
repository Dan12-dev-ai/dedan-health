/**
 * Jest setup — runs once per test file, after the test framework is installed.
 *
 * Registers the `@testing-library/jest-dom` matchers (`toBeInTheDocument`,
 * `toHaveAttribute`, ...). The package was already a devDependency but was not
 * referenced here, so those matchers did not exist and component tests could
 * not be written against the DOM.
 *
 * Kept in a dedicated file (rather than inlined into jest.config.cjs) so that
 * adding future global setup does not require adding a TypeScript transform
 * for the config file itself.
 */
import '@testing-library/jest-dom';
