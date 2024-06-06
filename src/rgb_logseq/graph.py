"""Logseq graph module."""

import pandas as pd
from pathlib import Path
from pydantic import BaseModel

from rgb_logseq.page import load_page_file

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
        logger.debug("Adding page to graph: %s", page.name)

        if duplicate := self.pages.get(page.name):
            if duplicate.is_placeholder:
                logger.debug("Overwriting placeholder entry: %s", page.name)
            else:
                logger.error("Adding page already in graph: %s", page.name)
                raise DuplicatePageNameError(page.name)

        self.pages[page.name] = page

        if page.namespace != NAMESPACE_SELF and page.namespace not in self.pages:
            self.add_placeholder(page.namespace)

        missing_links = [
            link.target for link in page.links if link.target not in self.pages
        ]
        self.add_placeholders(missing_links)

        missing_tags = [tag for tag in page.tags if tag not in self.pages]
        self.add_placeholders(missing_tags)

        missing_page_props = [
            prop for prop in page.properties if prop not in self.pages
        ]
        self.add_placeholders(missing_page_props)

        for block in page.blocks:
            missing_props = [
                block_prop
                for block_prop in block.properties
                if block_prop not in self.pages
            ]
            self.add_placeholders(missing_props)

    def add_placeholder(self, page_name: str) -> None:
        """Remember a Page name without requiring a full Page."""
        placeholder = Page(
            name=page_name,
            blocks=[],
            properties={},
            is_placeholder=True,
        )
        self.add_page(placeholder)

    def add_placeholders(self, page_names: list[str]) -> None:
        """Add placeholder for each name in the provided list."""
        for page_name in page_names:
            self.add_placeholder(page_name)

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


def load_graph(graph_path: Path) -> Graph:
    """Load pages in Graph."""
    logger.debug("path: %s", graph_path)
    page_folders = ["journals", "pages"]
    page_glob = "./**/*.md"
    graph = Graph()

    for folder in page_folders:
        subfolder = graph_path / folder
        for md_path in subfolder.glob(page_glob):
            logger.debug("md path: %s", md_path)
            page = load_page_file(md_path)
            logger.debug("page: %s", page)
            graph.add_page(page)

    return graph


def load_graph_blocks(graph: Graph) -> dict[str, pd.DataFrame]:
    """Load block info from the graph."""
    blocks = []
    links = []
    page_memberships = []
    block_properties = []

    for page_name, page in graph.pages.items():
        for position, block_info in enumerate(page.blocks):
            block_id = str(block_info.id)
            blocks.append(
                {
                    "uuid": block_id,
                    "content": block_info.content,
                    "is_heading": block_info.is_heading,
                    "directive": block_info.directive,
                }
            )
            page_memberships.append(
                {
                    "block": block_id,
                    "page": page_name,
                    "position": position,
                    "depth": block_info.depth,
                }
            )

            for link in block_info.links:
                links.append({"source": block_id, "target": link.target})

            for prop_name, prop in block_info.properties.items():
                block_properties.append(
                    {
                        "block": block_id,
                        "prop": prop_name,
                        "value": prop.value,
                    }
                )

    return {
        "blocks": pd.DataFrame(blocks),
        "links": pd.DataFrame(links),
        "page_memberships": pd.DataFrame(page_memberships),
        "block_properties": pd.DataFrame(block_properties),
    }


def load_graph_pages(graph: Graph) -> dict[str, pd.DataFrame]:
    """Load page info from the graph."""
    pages = []
    namespaces = []
    page_properties = []
    tags = []

    for page in graph.pages.values():
        pages.append(
            {
                "name": page.name,
                "is_placeholder": page.is_placeholder,
                "is_public": page.is_public,
            }
        )

        if page.namespace != NAMESPACE_SELF:
            namespaces.append({"page": page.name, "namespace": page.namespace})

        for tag in page.tags:
            tags.append({"page": page.name, "tag": tag})

        for prop_name, page_prop in page.properties.items():
            page_properties.append(
                {
                    "page": page.name,
                    "property": prop_name,
                    "value": page_prop.value,
                }
            )

    return {
        "pages": pd.DataFrame(pages),
        "namespaces": pd.DataFrame(namespaces),
        "page_properties": pd.DataFrame(page_properties),
        "tags": pd.DataFrame(tags),
    }
