// This file is a setup script for Vitest. It is executed before running
// the test suite. It imports the MSW server and sets up hooks to:
// 1. Start the server before all tests.
// 2. Reset handlers after each test to ensure test isolation.
// 3. Close the server after all tests are done.
// It also configures the server to throw an error for any unhandled requests,
// which helps catch unexpected API calls during tests.

import { server } from "./src/mocks/server";

beforeAll(() => server.listen({ onUnhandledRequest: "error" }));

afterEach(() => server.resetHandlers());

afterAll(() => server.close());
