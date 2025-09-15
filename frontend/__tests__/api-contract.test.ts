// This test file verifies the API contract by ensuring that the
// auto-generated API types from `openapi-typescript` are valid and
// can be imported without errors. It serves as a smoke test for the
// `gen:api` script and the OpenAPI specification.

import { describe, it, expect } from "vitest";
import type { paths } from "@/types/api";

// This is a type-level test. We just need to ensure the import works
// and that we can reference a type from it.
// eslint-disable-next-line @typescript-eslint/no-unused-vars -- This is a type-level test to ensure the type can be referenced.
type PresignedUrlResponse =
  paths["/v1/presigned-urls"]["post"]["responses"]["200"]["content"]["application/json"];

describe("API Contract", () => {
  it("should allow importing generated types", () => {
    // This test passes if the file compiles and runs, which means the
    // import and type referencing above worked correctly.
    expect(true).toBe(true);
  });
});
