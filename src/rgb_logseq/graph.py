"""Logseq graph module."""

from pydantic import BaseModel

from .page import Page


class PropertyInputError(Exception):
    """Error raised when a property string is not in ``key:: value` form."""


class EmptyBlockLinesError(Exception):
    """Error raised when a block is created with no lines."""


class Graph(BaseModel):
    """An organized collection of pages."""

    pages: dict[str, Page] = {}

    def add_page(self, page: Page) -> None:
        """Add a Page to the Graph."""
        self.pages[page.name] = page

    @property
    def links(self) -> list[dict[str, str]]:
        connections = []

        for page in self.pages.values():
            for link in page.links:
                if link.target in self.pages:
                    connections.append({"from": page.name, "to": link.target})

        return connections
