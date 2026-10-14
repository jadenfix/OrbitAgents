"""Provider boundary regression; no claim of live OpenSearch integration."""

import asyncio
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "services/query"))
from opensearch_client import OpenSearchClient, SearchUnavailableError  # noqa: E402
from schemas import SearchFilters  # noqa: E402


def test_unconfigured_provider_never_reports_successful_zero_matches():
    client = OpenSearchClient()

    async def unavailable():
        return False

    client.health_check = unavailable
    with pytest.raises(SearchUnavailableError):
        asyncio.run(client.search_properties(SearchFilters()))


def test_connected_transport_failure_never_reports_successful_zero_matches():
    client = OpenSearchClient()

    async def healthy():
        return True

    class BrokenTransport:
        def search(self, **kwargs):
            raise OSError("Provider connection closed")

    client.health_check = healthy
    client.client = BrokenTransport()
    with pytest.raises(SearchUnavailableError):
        asyncio.run(client.search_properties(SearchFilters()))
    assert client.error_count == 1
