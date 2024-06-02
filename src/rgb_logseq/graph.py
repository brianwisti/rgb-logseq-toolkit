"""Logseq graph module."""

from pydantic import BaseModel

from .const import logger
from .page import Page


class DuplicatePageNameError(Exception):
    """Error raised when overwriting an existing Page in a Graph."""


class PropertyInputError(Exception):
    """Error raised when a property string is not in ``key:: value` form."""


class EmptyBlockLinesError(Exception):
    """Error raised when a block is created with no lines."""


class Graph(BaseModel):
    """An organized collection of pages."""

    pages: dict[str, Page] = {}

    @property
    def page_properties(self) -> dict[str, list[Page]]:
        """Return information about all page-level properties in the graph."""
        properties: dict[str, list[Page]] = {}

        for page in self.pages.values():
            for prop in page.properties:
                prop_pages = properties.get(prop, [])
                prop_pages.append(page)
                properties[prop] = prop_pages

        return properties

    def add_page(self, page: Page) -> None:
        """Add a Page to the Graph."""
        logger.info("Adding page to graph: %s", page.name)

        if duplicate := self.pages.get(page.name):
            if duplicate.is_placeholder:
                logger.info("Overwriting placeholder entry: %s", page.name)
            else:
                logger.error("Adding page already in graph: %s", page.name)
                raise DuplicatePageNameError(page.name)

        self.pages[page.name] = page

        for link in page.links:
            if link.target not in self.pages:
                self.add_placeholder(link.target)

    def add_placeholder(self, page_name: str) -> None:
        """Remember a Page name without requiring a full Page."""
        placeholder = Page(
            name=page_name,
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
