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