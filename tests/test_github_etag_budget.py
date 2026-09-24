"""Tests for GitHub PAT ETag conditional requests and request budgeting (GH-54, GH-62)."""

from __future__ import annotations

import urllib.error
from unittest.mock import MagicMock, patch


from rebalance.ingest._http import GitHubClient


def test_github_client_headers_with_etag():
    client = GitHubClient("fake-token")
    headers = client.headers(etag='"12345abcdef"')
    assert headers["If-None-Match"] == '"12345abcdef"'
    assert headers["Authorization"] == "Bearer fake-token"


def test_github_client_304_not_modified():
    client = GitHubClient("fake-token", retries=2, run_id="test-run-304")
    # Simulate urllib HTTPError with code 304
    http_error = urllib.error.HTTPError(
        url="https://api.github.com/repos/test/test",
        code=304,
        msg="Not Modified",
        hdrs={"etag": '"12345abcdef"', "x-ratelimit-remaining": "4999"},
        fp=None,
    )

    with patch("urllib.request.urlopen", side_effect=http_error) as mock_urlopen:
        status, data, headers = client.get_with_headers("/repos/test/test", etag='"12345abcdef"')
        assert status == 304
        assert data is None
        assert headers.get("etag") == '"12345abcdef"'

        # Assert outgoing Request passed to urlopen carried the If-None-Match header
        assert mock_urlopen.call_count == 1
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("If-none-match") == '"12345abcdef"'

    summary = client.request_summary()
    assert summary["not_modified_requests"] == 1
    assert summary["logical_requests"] == 1


def test_github_client_200_with_etag():
    client = GitHubClient("fake-token", run_id="test-run-200")
    mock_resp = MagicMock()
    mock_resp.status = 200
    mock_resp.read.return_value = b'{"name": "test-repo"}'
    mock_resp.headers = {"etag": '"new-etag-67890"', "x-ratelimit-remaining": "4998"}
    mock_resp.__enter__.return_value = mock_resp

    with patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen:
        status, data, headers = client.get_with_headers("/repos/test/test", etag='"old-etag"')
        assert status == 200
        assert data == {"name": "test-repo"}
        assert headers.get("etag") == '"new-etag-67890"'

        # Assert outgoing Request carried the If-None-Match header
        assert mock_urlopen.call_count == 1
        req = mock_urlopen.call_args[0][0]
        assert req.get_header("If-none-match") == '"old-etag"'
