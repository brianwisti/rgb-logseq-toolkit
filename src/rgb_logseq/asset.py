"""Logseq asset file handling."""

from pathlib import Path

from pydantic import BaseModel


class Asset(BaseModel):
    """A Logseq asset file."""

    path: Path

    @property
    def name(self) -> str:
        """Return the asset file name."""
        return self.path.stem
