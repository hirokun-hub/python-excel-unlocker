# This file contains tests for the presigned URL generation logic.
# It uses moto to mock S3 and ensures that the generate_presigned_url
# function behaves as expected without making real AWS calls.

import pytest
from backend.src import main as main_app

# Define test constants
TEST_BUCKET = "test-bucket"
TEST_REGION = "us-east-1"

@pytest.fixture
def s3_setup(monkeypatch, mock_s3):
    """Set up the S3 bucket and environment variables for the tests."""
    monkeypatch.setenv("S3_BUCKET_NAME", TEST_BUCKET)
    monkeypatch.setenv("AWS_REGION", TEST_REGION)
    mock_s3.create_bucket(Bucket=TEST_BUCKET)
    # Reload the main_app to re-initialize the s3_client with the mocked env
    # This is not ideal, but avoids major refactoring of main.py
    import importlib
    importlib.reload(main_app)


def test_generate_presigned_url_put(s3_setup):
    """
    Tests that a valid presigned URL for a PUT operation is generated.
    """
    filename = "test-file.xlsx"
    s3_key = f"uploads/{filename}"

    url = main_app.generate_presigned_url(
        bucket=TEST_BUCKET,
        key=s3_key,
        client_method='put_object',
        expires_in=3600
    )

    assert url is not None
    assert isinstance(url, str)
    assert "s3.amazonaws.com" in url
    assert f"/{TEST_BUCKET}/{s3_key}" in url
    assert "X-Amz-Algorithm=AWS4-HMAC-SHA256" in url
    assert "X-Amz-Credential=" in url
    assert "X-Amz-Expires=3600" in url
    assert "X-Amz-Signature=" in url

def test_generate_presigned_url_get(s3_setup):
    """
    Tests that a valid presigned URL for a GET operation is generated.
    """
    s3_key = "unlocked/test-file.xlsx"

    url = main_app.generate_presigned_url(
        bucket=TEST_BUCKET,
        key=s3_key,
        client_method='get_object',
        expires_in=1800
    )

    assert url is not None
    assert "s3.amazonaws.com" in url
    assert f"/{TEST_BUCKET}/{s3_key}" in url
    assert "X-Amz-Expires=1800" in url
