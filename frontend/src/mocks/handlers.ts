// This file defines the mock API handlers for use with MSW (Mock Service Worker).
// These handlers intercept HTTP requests during testing and development,
// returning mocked responses instead of hitting a real backend. This allows for
// isolated frontend testing and development.

import { http, HttpResponse } from "msw";

const API_BASE_URL = "http://127.0.0.1:4010";

export const handlers = [
  // Mock for getting a presigned URL
  http.post(`${API_BASE_URL}/v1/presigned-urls`, () => {
    return HttpResponse.json({
      ok: true,
      data: {
        upload_url: "http://localhost:9000/mock-bucket/upload-url",
        s3_key: "mocks/12345.xlsx",
      },
      error: null,
    });
  }),

  // Mock for starting the unlock process
  http.post(`${API_BASE_URL}/v1/unlock`, () => {
    return HttpResponse.json(
      {
        ok: true,
        data: { job_id: "mock-job-123" },
        error: null,
      },
      { status: 202 },
    );
  }),

  // Mock for checking job status
  http.get(`${API_BASE_URL}/v1/status/:job_id`, () => {
    return HttpResponse.json({
      ok: true,
      data: {
        status: "completed",
        download_url: "http://localhost:9000/mock-bucket/download-url",
      },
      error: null,
    });
  }),
];
