"""Logseq asset file handling."""

from pathlib import Path

from pydantic import BaseModel


class Asset(BaseModel):
    """A Logseq asset file."""

    path: Path

    @property
    def exists(self) -> bool:
        """Return whether the asset file exists."""
        return self.path.exists()

    @property
    def name(self) -> str:
        """Return the asset file name as identified by page links."""
        return f"../assets/{self.path.name}"
