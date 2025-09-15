# Excel Password Remover

This project is an API to remove passwords from Excel files.
It is built with AWS Lambda, API Gateway, and S3 for the backend.

## Structure

- `backend/`: Source code for the AWS Lambda function.
- `frontend/`: Next.js frontend application.
- `docs/`: Project documentation.
- `scripts/`: Old or utility scripts.

## Frontend Features

### Google Drive Integration

- After processing your files, you can save them directly to your Google Drive.
- **Selecting a Destination Folder**:
  1. Once the results are shown, a "Google Drive Destination" bar will appear.
  2. Click the "Select Destination" (保存先を選ぶ) button.
  3. A folder picker will open, allowing you to navigate and search your Google Drive folders.
  4. Choose a folder and click "Pick this folder" (このフォルダを選ぶ).
- Your folder choice is saved in your browser and will be remembered for future sessions. You can clear the selection at any time.
- If no folder is selected, files will be saved to the root of your "My Drive".

## Development and Testing

This project is configured with a complete local testing and CI environment to allow for independent frontend and backend development.

### Prerequisites

- **Node.js**: v20 or later
- **Python**: v3.11 or later
- **npm**: (should come with Node.js)

### Backend Development

1.  **Install Dependencies**:
    ```bash
    # Install production and development dependencies
    pip install -r backend/src/requirements.txt -r backend/requirements-dev.txt
    ```

2.  **Run Tests**:
    The backend tests use `pytest` and `moto` to mock AWS services.
    ```bash
    # Run from the root of the repository
    PYTHONPATH=. pytest backend/tests/
    ```

### Frontend Development

1.  **Install Dependencies**:
    ```bash
    # Install dependencies from the lockfile
    npm ci --prefix frontend
    ```

2.  **Generate API Types**:
    The frontend uses types generated from the OpenAPI specification.
    ```bash
    npm run gen:api --prefix frontend
    ```

3.  **Run the Mock API Server**:
    For UI development without a live backend, you can use the Prism mock server, which serves responses based on `api/openapi.yaml`.
    ```bash
    # Start the server in the background
    npm run mock:api --prefix frontend &
    echo $! > prism.pid

    # To stop the server
    kill $(cat prism.pid)
    ```

4.  **Run Tests**:
    The frontend has unit/integration tests using Vitest and MSW.
    ```bash
    # Run Vitest tests
    npm test --prefix frontend

    # Run Playwright UI smoke tests
    npm run test:ui --prefix frontend
    ```

### CI/CD Pipelines

The project uses three separate GitHub Actions workflows to validate changes:

-   **`Backend CI`**: Lints, tests, and validates the backend code and OpenAPI spec. On success, it uploads the `openapi.yaml` file as an artifact named `openapi-v1`.
-   **`Frontend CI`**: Lints, tests (unit and UI), and validates the frontend application against a mock API server.
-   **`Contract Check`**: Triggered by a successful `Backend CI` run. It downloads the `openapi-v1` artifact and compares it with the current version to prevent breaking API changes.

All workflows produce a `test-report_*.zip` artifact containing a Markdown summary of the run.