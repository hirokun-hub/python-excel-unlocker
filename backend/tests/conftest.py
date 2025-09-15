# This file contains shared fixtures for pytest.
# It sets up a mock S3 environment using moto, ensuring that tests
# do not interact with actual AWS resources. It also configures
# necessary environment variables for the tests.

import boto3
import pytest
from moto import mock_aws

@pytest.fixture(scope="function")
def aws_credentials(monkeypatch):
    """Mocked AWS Credentials for moto."""
    monkeypatch.setenv("AWS_ACCESS_KEY_ID", "testing")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "testing")
    monkeypatch.setenv("AWS_SECURITY_TOKEN", "testing")
    monkeypatch.setenv("AWS_SESSION_TOKEN", "testing")
    monkeypatch.setenv("AWS_DEFAULT_REGION", "us-east-1")

@pytest.fixture(scope="function")
def mock_s3(aws_credentials):
    """Set up a mock S3 environment."""
    with mock_aws():
        yield boto3.client("s3", region_name="us-east-1")
