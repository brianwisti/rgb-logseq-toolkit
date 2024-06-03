"""Logseq graph module."""

from pydantic import BaseModel

from .const import logger
from .page import NAMESPACE_SELF, Page


class DuplicatePageNameError(Exception):
    """Error raised when overwriting an existing Page in a Graph."""


class PropertyInputError(Exception):
    """Error raised when a property string is not in ``key:: value` form."""


class EmptyBlockLinesError(Exception):
    """Error raised when a block is created with no lines."""


PagePropertyMap = dict[str, dict[str, str]]


class Graph(BaseModel):
    """An organized collection of pages."""

    pages: dict[str, Page] = {}

    @property
    def page_properties(self) -> PagePropertyMap:
        """Return information about all page-level properties in the graph."""
        properties: PagePropertyMap = {}

        for page in self.pages.values():
            for prop_name, prop in page.properties.items():
                prop_pages = properties.get(prop_name, {})
                prop_pages[page.name] = prop.value
                properties[prop_name] = prop_pages

        return properties

    @property
    def page_tags(self) -> dict[str, list[str]]:
        """Return information about all tags in the graph."""
        tags: dict[str, list[str]] = {}

        for page_name, page in self.pages.items():
            for tag in page.tags:
                page_list = tags.get(tag, [])
                page_list.append(page_name)
                tags[tag] = page_list

        return tags

    def add_page(self, page: Page) -> None:
        """Add a Page to the Graph."""
        logger.info("Adding page to graph: %s", page.name)

        if duplicate := self.pages.get(page.name):
            if duplicate.is_placeholder:
                logger.debug("Overwriting placeholder entry: %s", page.name)
            else:
                logger.error("Adding page already in graph: %s", page.name)
                raise DuplicatePageNameError(page.name)

        self.pages[page.name] = page

        if page.namespace != NAMESPACE_SELF and page.namespace not in self.pages:
            self.add_placeholder(page.namespace)

        for link in page.links:
            if link.target not in self.pages:
                self.add_placeholder(link.target)

        for tag in page.tags:
            if tag not in self.pages:
                self.add_placeholder(tag)

        for prop in page.properties:
            if prop not in self.pages:
                self.add_placeholder(prop)

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
