// This file contains a mock integration test that simulates a full user
// flow against the MSW mock server. It verifies that the frontend can
// interact with the API contract as expected, from getting a presigned
// URL to starting the unlock process.

import { describe, it, expect } from "vitest";
import axios from "axios";
import type { paths } from "@/types/api";

const API_BASE_URL = "http://127.0.0.1:4010";

describe("API Mock Integration", () => {
  it("should simulate a successful unlock flow", async () => {
    // 1. Get a presigned URL
    const presignedUrlResponse = await axios.post<
      paths["/v1/presigned-urls"]["post"]["responses"]["200"]["content"]["application/json"]
    >(`${API_BASE_URL}/v1/presigned-urls`, { filename: "test.xlsx" });

    expect(presignedUrlResponse.status).toBe(200);
    expect(presignedUrlResponse.data.ok).toBe(true);
    expect(presignedUrlResponse.data.data?.s3_key).toBe("mocks/12345.xlsx");
    const s3_key = presignedUrlResponse.data.data?.s3_key;

    // Assume file is uploaded to the received upload_url...

    // 2. Call the unlock endpoint with the s3_key
    const unlockResponse = await axios.post<
      paths["/v1/unlock"]["post"]["responses"]["202"]["content"]["application/json"]
    >(`${API_BASE_URL}/v1/unlock`, {
      s3_key: s3_key,
      passwords: ["password123"],
    });

    expect(unlockResponse.status).toBe(202);
    expect(unlockResponse.data.ok).toBe(true);
    expect(unlockResponse.data.data?.job_id).toBe("mock-job-123");
  });
});
