"""Logseq graph module."""

from pydantic import BaseModel

from .const import logger
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
        logger.info("Adding page to graph: %s", page.name)

        if duplicate := self.pages.get(page.name):
            if duplicate.is_placeholder:
                logger.info("Overwriting placeholder entry: %s", page.name)
            else:
                logger.warning("Overwriting duplicate named entry: %s", page.name)

        self.pages[page.name] = page

        for link in page.links:
            if link.target not in self.pages:
                placeholder = Page(
                    name=link.target,
                    blocks=[],
                    properties={},
                    is_placeholder=True,
                )
                self.add_page(placeholder)

    def has_page(self, page_name: str) -> bool:
        """Return True if a Page with matching name has been added."""
        return page_name in self.pages

    @property
    def links(self) -> list[dict[str, str]]:
        connections = []

        for page in self.pages.values():
            logger.debug(page)

            for link in page.links:
                connections.append({"from": page.name, "to": link.target})

        return connections
