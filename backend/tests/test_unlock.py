# This file contains tests for the Excel file unlocking logic.
# It uses moto to mock S3 and unittest.mock to patch the decryption
# library, allowing for isolated testing of the unlock workflow,
# including logging and error handling.

import os
import pytest
import msoffcrypto
from unittest.mock import patch, MagicMock
from backend.src import main as main_app

# Define test constants
TEST_BUCKET = "test-bucket"
TEST_REGION = "us-east-1"
FIXTURE_DIR = os.path.join(os.path.dirname(__file__), 'fixtures')

@pytest.fixture
def s3_setup(monkeypatch, mock_s3):
    """Set up the S3 bucket and environment variables for the tests."""
    monkeypatch.setenv("S3_BUCKET_NAME", TEST_BUCKET)
    monkeypatch.setenv("AWS_REGION", TEST_REGION)
    mock_s3.create_bucket(Bucket=TEST_BUCKET)

    # Upload the dummy file to mock S3
    dummy_file_path = os.path.join(FIXTURE_DIR, 'sample_protected.xlsx')
    with open(dummy_file_path, 'rb') as f:
        mock_s3.put_object(Bucket=TEST_BUCKET, Key="test.xlsx", Body=f.read())

    # Reload main_app to ensure it uses the mocked environment
    import importlib
    importlib.reload(main_app)

    return mock_s3


def test_unlock_file_success(s3_setup, caplog):
    """
    Tests the successful unlocking of a file.
    Mocks the decryption library to simulate a correct password.
    """
    mock_office_file = MagicMock()
    # The first password 'good_pass' will succeed.
    mock_office_file.load_key.side_effect = [None]

    with patch('msoffcrypto.OfficeFile', return_value=mock_office_file):
        # The function expects a local file path, so we'll create a dummy one
        dummy_local_path = "/tmp/dummy_file.xlsx"
        with open(dummy_local_path, "w") as f:
            f.write("dummy content")

        result = main_app.unlock_excel_file(
            file_path=dummy_local_path,
            passwords=["good_pass", "bad_pass"]
        )

        # Assertions
        assert result['success'] is True
        assert 'unlocked_file_path' in result
        assert result['password_used'] == 'good_pass'

        # Verify logging
        assert "Trying password: ******" in caplog.text
        assert "Password correct." in caplog.text

        # Verify mocks were called
        mock_office_file.load_key.assert_called_once_with(password="good_pass")
        mock_office_file.decrypt.assert_called_once()

        os.remove(dummy_local_path)
        os.remove(result['unlocked_file_path'])


def test_unlock_file_failure(s3_setup, caplog):
    """
    Tests the failure case where all passwords are incorrect.
    Mocks the decryption library to simulate only invalid passwords.
    """
    mock_office_file = MagicMock()
    # Both passwords will raise InvalidKeyError
    mock_office_file.load_key.side_effect = [
        msoffcrypto.exceptions.InvalidKeyError,
        msoffcrypto.exceptions.InvalidKeyError
    ]

    with patch('msoffcrypto.OfficeFile', return_value=mock_office_file):
        dummy_local_path = "/tmp/dummy_file.xlsx"
        with open(dummy_local_path, "w") as f:
            f.write("dummy content")

        result = main_app.unlock_excel_file(
            file_path=dummy_local_path,
            passwords=["bad_pass1", "bad_pass2"]
        )

        # Assertions
        assert result['success'] is False
        assert result['message'] == 'All provided passwords failed to unlock the file.'

        # Verify logging
        # Two attempts should be logged
        assert caplog.text.count("Trying password: ******") == 2
        assert "Invalid password, trying next one." in caplog.text
        assert "All passwords failed." in caplog.text

        # Verify mocks were called
        assert mock_office_file.load_key.call_count == 2
        mock_office_file.decrypt.assert_not_called()

        os.remove(dummy_local_path)
