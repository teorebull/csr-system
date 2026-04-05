from __future__ import annotations


class PageFetcher:
    """Base wrapper for downloading and cleaning evidence pages."""

    def fetch(self, url: str) -> str:
        raise NotImplementedError
