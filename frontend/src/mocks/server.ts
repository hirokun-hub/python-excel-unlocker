// This file sets up the MSW server for Node.js environments (like Vitest).
// It imports the handlers and exports the configured server instance, which
// will be used in the Vitest setup file to intercept requests during tests.

import { setupServer } from "msw/node";
import { handlers } from "./handlers";

export const server = setupServer(...handlers);
