"""Logseq graph module."""

import uuid
from pathlib import Path
from typing import cast

from pydantic import BaseModel

from rgb_logseq.page import load_page_file

from .asset import Asset
from .block import Block
from .const import logger
from .page import NAMESPACE_SELF, Page


class DuplicateAssetError(Exception):
    """Error raised when overwriting an existing asset in a Graph."""


class DuplicatePageNameError(Exception):
    """Error raised when overwriting an existing Page in a Graph."""


class PropertyInputError(Exception):
    """Error raised when a property string is not in ``key:: value` form."""


class EmptyBlockLinesError(Exception):
    """Error raised when a block is created with no lines."""


PagePropertyMap = dict[str, dict[str, str]]


class Graph(BaseModel):
    """An organized collection of pages."""

    blocks: dict[uuid.UUID, Block] = {}
    pages: dict[str, Page] = {}
    assets: dict[str, Asset] = {}

    @property
    def asset_links(self) -> list[dict[str, object]]:
        """Return all asset links in the graph."""
        asset_links = []

        for page in self.pages.values():
            for block in page.blocks:
                for resource_link in block.resource_links:
                    if resource_link.target in self.assets:
                        asset_links.append(
                            {"source": block.id, "target": resource_link.target}
                        )

        return asset_links

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

    def add_asset(self, path: Path) -> Asset:
        """Add an asset to the Graph."""
        logger.debug("Adding asset to graph: %s", path)
        asset = Asset(path=path)

        if asset.name in self.assets:
            logger.error("Adding duplicate asset: %s", path)
            raise DuplicateAssetError(asset.name)

        self.assets[asset.name] = asset

        return asset

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
        placeholders_needed = []

        if page.namespace != NAMESPACE_SELF and page.namespace not in self.pages:
            placeholders_needed.append(page.namespace)

        placeholders_needed += [
            link.target for link in page.links if link.target not in self.pages
        ]

        for block in page.blocks:
            block_id = cast(uuid.UUID, block.id)
            self.blocks[block_id] = block

            for tag_link in block.tag_links:
                if tag_link.target not in self.pages:
                    placeholders_needed.append(tag_link.target)

        placeholders_needed += [tag for tag in page.tags if tag not in self.pages]

        placeholders_needed += [
            prop for prop in page.properties if prop not in self.pages
        ]

        for block in page.blocks:
            placeholders_needed += [
                block_prop
                for block_prop in block.properties
                if block_prop not in self.pages
            ]

        self.add_placeholders(placeholders_needed)

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
    asset_folders = ["assets"]
    page_folders = ["journals", "pages"]
    page_glob = "./**/*.md"
    graph = Graph()

    for page_folder in page_folders:
        subfolder = graph_path / page_folder
        for md_path in subfolder.glob(page_glob):
            logger.debug("md path: %s", md_path)
            page = load_page_file(md_path)
            logger.debug("page: %s", page)
            graph.add_page(page)

    for asset_folder in asset_folders:
        subfolder = graph_path / asset_folder
        for asset_path in subfolder.glob("*"):
            graph.add_asset(asset_path)

    logger.info("Loaded graph %s; %s pages", graph_path.stem, len(graph.pages))

    return graph

