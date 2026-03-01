"""
Unit tests for config.settings.validate_cors_origins().

Verifies that the CORS startup guard:
  - accepts well-formed origin lists (including localhost and HTTPS origins)
  - rejects an empty list
  - rejects any list that contains the wildcard '*'
  - provides a descriptive error message in both failure cases

No AWS credentials or network access required.
"""

import sys

sys.path.insert(0, ".")

import pytest
from config.settings import validate_cors_origins

pytestmark = pytest.mark.unit


class TestValidCorsOrigins:
    """validate_cors_origins() must not raise for legitimate origin lists."""

    def test_single_localhost_origin(self):
        validate_cors_origins(["http://localhost:8501"])

    def test_single_https_origin(self):
        validate_cors_origins(["https://koda.example.com"])

    def test_multiple_https_origins(self):
        validate_cors_origins(
            [
                "https://koda.example.com",
                "https://koda-staging.example.com",
            ]
        )

    def test_localhost_and_production_together(self):
        validate_cors_origins(
            [
                "http://localhost:8501",
                "https://koda.example.com",
            ]
        )

    def test_cloudfront_domain(self):
        validate_cors_origins(["https://d1a2b3c4xyz.cloudfront.net"])


class TestEmptyCorsOrigins:
    """An empty origin list must raise ValueError with a helpful message."""

    def test_empty_list_raises(self):
        with pytest.raises(ValueError, match="CORS_ALLOWED_ORIGINS is empty"):
            validate_cors_origins([])

    def test_error_message_mentions_example(self):
        """Error message should guide the operator to the correct fix."""
        with pytest.raises(ValueError, match="comma-separated"):
            validate_cors_origins([])


class TestWildcardCorsOrigins:
    """A wildcard '*' in the origin list must raise ValueError."""

    def test_bare_wildcard_raises(self):
        with pytest.raises(ValueError, match=r"must not contain the wildcard"):
            validate_cors_origins(["*"])

    def test_wildcard_mixed_with_real_origins_raises(self):
        """Even one '*' in an otherwise valid list must be rejected."""
        with pytest.raises(ValueError, match=r"must not contain the wildcard"):
            validate_cors_origins(["https://koda.example.com", "*"])

    def test_wildcard_first_raises(self):
        with pytest.raises(ValueError, match=r"must not contain the wildcard"):
            validate_cors_origins(["*", "https://koda.example.com"])

    def test_error_message_mentions_owasp(self):
        """Error must cite OWASP A05:2021 to explain the security rationale."""
        with pytest.raises(ValueError, match="OWASP A05:2021"):
            validate_cors_origins(["*"])

    def test_error_message_suggests_explicit_origin(self):
        with pytest.raises(ValueError, match="Specify explicit origins"):
            validate_cors_origins(["*"])
