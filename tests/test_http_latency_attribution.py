"""Per-request wall time in the GitHub job summary (GH-59 follow-up, P-003).

Why this exists rather than a throttle. Issue #62 held that the hourly `github-sync` job
exhausts the 5,000/hr REST budget in under fifteen minutes, and the proposed fix was to slow it
down. Two things were then observed about a real scheduled run: the process sat blocked in
`poll()` inside an SSL read from api.github.com for tens of minutes at a time, and sampling
`GET /rate_limit` suggested it was spending almost no quota.

Only the first of those survived. `GET /rate_limit` turned out not to report the bucket that
gates requests at all — probed directly, it read `core: used=47` while a `/user` call in the
same second returned 403 with `x-ratelimit-used: 5000` on `core` and a *different* reset epoch.
Two buckets, not a lag. So the quota question is genuinely open, and the latency question is
answered only to the extent that one `sample(1)` of a stalled process answers it.

What both halves have in common is that the existing attribution could not settle either. It
counted requests, attempts and endpoints and never timed anything, and it kept the first and
last rate-limit header sample rather than the lowest — so a slow run looked idle and an
exhausted budget could pass through unrecorded between two healthy samples.

These tests pin the timing dimension, the two properties that make the number trustworthy
(retry backoff excluded, a request that never answers still measured), and the trough-tracking
that attributes exhaustion to an endpoint. The point is instruments that read what is actually
enforced — measuring the wrong counter for an hour is what put this section in the plan doc
twice.
"""

from __future__ import annotations

import unittest
import urllib.error
from unittest.mock import patch

from rebalance.ingest import _http
from rebalance.ingest._http import GitHubClient


class _FakeResponse:
    """Minimal urlopen context manager whose read() can take a controllable amount of time."""

    def __init__(self, clock, body="{}", status=200, headers=None, seconds=0.0):
        self._clock = clock
        self._body = body
        self.status = status
        self.headers = headers or {}
        self._seconds = seconds

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    def read(self):
        self._clock.advance(self._seconds)
        return self._body.encode()


class _Clock:
    """A monotonic clock the test drives, so timings are exact rather than flaky."""

    def __init__(self):
        self.now = 1000.0

    def advance(self, seconds):
        self.now += seconds

    def __call__(self):
        return self.now


def _client(**kwargs):
    # A distinct job label per test keeps the process-global attribution registry from
    # sharing state between tests.
    return GitHubClient("token", **kwargs)


class LatencyRecordedTests(unittest.TestCase):
    def setUp(self):
        self.clock = _Clock()
        patcher = patch.object(_http.time, "monotonic", self.clock)
        patcher.start()
        self.addCleanup(patcher.stop)
        _http._JOB_ATTRIBUTION.clear()

    def test_a_slow_request_is_timed_and_named(self):
        """The observed shape: one endpoint, one request, tens of minutes inside the read."""
        response = _FakeResponse(self.clock, seconds=1800.0)
        with patch.object(_http.urllib.request, "urlopen", return_value=response):
            client = _client()
            client.get("/repos/acme/widgets/events")

        summary = client.request_summary()
        self.assertEqual(summary["total_seconds"], 1800.0)
        self.assertEqual(summary["endpoint_seconds"]["/repos/{owner}/{repo}/events"], 1800.0)
        self.assertEqual(summary["slowest_requests"][0]["endpoint"], "/repos/{owner}/{repo}/events")

    def test_a_low_request_count_no_longer_hides_a_long_run(self):
        """The exact misreading this instrumentation exists to prevent.

        Two requests looks like a job doing nearly nothing, which is what the request counts
        said while the run took half an hour. The count and the duration must disagree, and
        the summary must carry both.
        """
        with patch.object(
            _http.urllib.request, "urlopen", side_effect=lambda *a, **k: _FakeResponse(self.clock, seconds=900.0)
        ):
            client = _client()
            client.get("/user/repos")
            client.get("/user/repos")

        summary = client.request_summary()
        self.assertEqual(summary["logical_requests"], 2, "still a tiny request count")
        self.assertEqual(summary["total_seconds"], 1800.0, "and still half an hour of wall time")

    def test_only_the_slowest_few_are_kept(self):
        """A full crawl makes thousands of requests; the summary is a log line."""
        with patch.object(
            _http.urllib.request, "urlopen", side_effect=lambda *a, **k: _FakeResponse(self.clock, seconds=1.0)
        ):
            client = _client()
            for index in range(20):
                client.get(f"/repos/acme/repo{index}/events")

        slowest = client.request_summary()["slowest_requests"]
        self.assertEqual(len(slowest), _http._SLOWEST_KEPT)

    def test_the_max_per_endpoint_survives_averaging(self):
        """One hung call among many fast ones is the signal; a total would dilute it."""
        durations = iter([0.1, 0.1, 600.0, 0.1])
        with patch.object(
            _http.urllib.request,
            "urlopen",
            side_effect=lambda *a, **k: _FakeResponse(self.clock, seconds=next(durations)),
        ):
            client = _client()
            for _ in range(4):
                client.get("/user/repos")

        self.assertEqual(client.request_summary()["endpoint_seconds_max"]["/user/repos"], 600.0)


class LatencyExcludesOurOwnWaitingTests(unittest.TestCase):
    """A duration that included our backoff would describe us, not GitHub."""

    def setUp(self):
        self.clock = _Clock()
        patcher = patch.object(_http.time, "monotonic", self.clock)
        patcher.start()
        self.addCleanup(patcher.stop)
        _http._JOB_ATTRIBUTION.clear()

    def test_retry_backoff_is_not_counted_as_server_latency(self):
        """A 503 retried after a 30s sleep must report the request time, not 30s+.

        Without this the instrumentation would confirm any theory it was pointed at: every
        retried request would look slow, and the slowest endpoints would simply be the ones
        that failed most.
        """
        error = urllib.error.HTTPError("https://api.github.com/user/repos", 503, "boom", {}, None)

        def raise_after(*_args, **_kwargs):
            self.clock.advance(2.0)  # the request itself
            raise error

        client = _client(retries=2)
        with (
            patch.object(_http.urllib.request, "urlopen", side_effect=raise_after),
            patch.object(client, "_sleep", side_effect=lambda seconds: self.clock.advance(30.0)),
        ):
            client.get("/user/repos")

        summary = client.request_summary()
        self.assertEqual(summary["total_seconds"], 4.0, "two attempts at 2s each, no backoff")

    def test_a_request_that_never_answers_is_still_timed(self):
        """A read that hangs until the socket timeout raises OSError, not HTTPError — it
        would have escaped untimed, and it is the most interesting sample there is."""

        def hang(*_args, **_kwargs):
            self.clock.advance(120.0)
            raise TimeoutError("timed out")

        client = _client(retries=1)
        with patch.object(_http.urllib.request, "urlopen", side_effect=hang):
            with self.assertRaises(TimeoutError):
                client.get("/user/repos")

        self.assertEqual(client.request_summary()["total_seconds"], 120.0)


class RemainingAttributionTests(unittest.TestCase):
    """`remaining=0` was real and unexplained. The summary now names who got it there."""

    def setUp(self):
        _http._JOB_ATTRIBUTION.clear()

    def test_the_lowest_remaining_and_its_endpoint_are_recorded(self):
        headers = iter(
            [
                {"x-ratelimit-remaining": "4900", "x-ratelimit-reset": "1"},
                {"x-ratelimit-remaining": "12", "x-ratelimit-reset": "1"},
                {"x-ratelimit-remaining": "4000", "x-ratelimit-reset": "1"},
            ]
        )
        clock = _Clock()
        with (
            patch.object(_http.time, "monotonic", clock),
            patch.object(
                _http.urllib.request,
                "urlopen",
                side_effect=lambda *a, **k: _FakeResponse(clock, headers=next(headers)),
            ),
        ):
            client = _client()
            client.get("/user/repos")
            client.get("/search/issues")
            client.get("/user/repos")

        limits = client.request_summary()["rate_limit_headers"]
        self.assertEqual(limits["remaining_min"], 12)
        self.assertEqual(
            limits["remaining_min_endpoint"],
            "/search/issues",
            "a first/last pair would have missed the trough entirely",
        )


if __name__ == "__main__":
    unittest.main()
