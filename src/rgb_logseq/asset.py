"""Logseq asset file handling."""

from pathlib import Path, PurePosixPath

from pydantic import BaseModel


class Asset(BaseModel):
    """A Logseq asset file."""

    path: PurePosixPath

    @property
    def exists(self) -> bool:
        """Return whether the asset file exists."""
        return Path(self.path).exists()

    @property
    def name(self) -> str:
        """Return the asset file name as identified by page links."""
        return f"../assets/{self.path.name}"
