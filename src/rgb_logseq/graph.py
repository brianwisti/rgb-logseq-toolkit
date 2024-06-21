"""Logseq graph module."""

import uuid
from pathlib import Path
from typing import cast

import pandas as pd
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


def load_graph_blocks(graph: Graph) -> dict[str, pd.DataFrame]:
    """Load block info from the graph."""
    blocks = []
    links = []
    tag_links: list[dict[str, str]] = []
    block_links: list[dict[str, str]] = []
    page_memberships = []
    block_properties = []
    block_branches = []
    assets = graph.assets
    resources_seen: dict[str, bool] = {}
    resources: list[dict[str, str | bool]] = []
    resource_links: list[dict[str, str]] = []

    for page_name, page in graph.pages.items():
        logger.debug("Loading graph blocks from page: %s", page_name)
        page_memberships += page.block_memberships_for_kuzu()

        # Building a map of newest branches seen at each level,
        # which provides an extremely narrow map of the tree from
        # the perspective of the current block.
        block_branches_seen: dict[int, str] = {}

        for position, block_info in enumerate(page.blocks):
            block_id = str(block_info.id)
            block_depth = block_info.depth
            block_branches_seen[block_depth] = block_id
            parent_depth = block_depth - 1

            if parent_depth in block_branches_seen:
                parent_id = block_branches_seen[parent_depth]
                block_branches.append({"uuid": block_id, "parent": parent_id, "position": position, "depth": block_info.depth})

            blocks.append(block_info.for_kuzu())

            for link in block_info.links:
                links.append({"source": block_id, "target": link.target})

            for resource_link in block_info.resource_links:
                target = resource_link.target
                is_asset = True if target in assets else False
                resources_seen[target] = is_asset
                resource_links.append(
                    {
                        "source": block_id,
                        "target": target,
                        "label": resource_link.link_text,
                    }
                )

            for tag_link in block_info.tag_links:
                tag_links.append({"source": block_id, "target": link.target})

            for block_link in block_info.block_links:
                if block_link.target in graph.blocks:
                    logger.debug(
                        "page <%s> links to block: %s", page_name, block_link.target
                    )
                    block_links.append(
                        {"source": block_id, "target": str(block_link.target)}
                    )
                else:
                    logger.warning(
                        "page <%s> links to nonexistent block <%s> in: %s",
                        page_name,
                        block_link.target,
                        block_info.content,
                    )

            for prop_name, prop in block_info.properties.items():
                block_properties.append(
                    {
                        "block": block_id,
                        "prop": prop_name,
                        "value": prop.value,
                    }
                )

    resources = [
        {"path": resource, "is_asset": is_asset}
        for resource, is_asset in resources_seen.items()
    ]
    return {
        "blocks": pd.DataFrame(blocks),
        "branches": pd.DataFrame(block_branches),
        "links": pd.DataFrame(links),
        "tag_links": pd.DataFrame(tag_links),
        "block_links": pd.DataFrame(block_links),
        "page_memberships": pd.DataFrame(page_memberships),
        "block_properties": pd.DataFrame(block_properties),
        "resources": pd.DataFrame(resources),
        "resource_links": pd.DataFrame(resource_links),
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
