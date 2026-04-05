from __future__ import annotations


class SearchClient:
    """Base wrapper for the selected search backend."""

    def search(self, query: str) -> list[dict]:
        raise NotImplementedError
