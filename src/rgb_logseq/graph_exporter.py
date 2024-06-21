"""Functionality for exporting a graph to Dataframes for Kuzu."""

from typing import cast

import pandas as pd
from pydantic import BaseModel

from .graph import Graph
from .page import NAMESPACE_SELF


class GraphExporter(BaseModel):
    """Transforms Graph information to DataFrames."""

    graph: Graph

    @property
    def block_branches(self) -> pd.DataFrame:
        """Return a DataFrame of all block branches in the graph."""
        branches = []

        for page in self.graph.pages.values():
            # Building a map of newest branches seen at each level,
            # which provides an extremely narrow map of the tree from
            # the perspective of the current block.
            block_branches_seen: dict[int, str] = {}

            for position, block in enumerate(page.blocks):
                block_id = str(block.id)
                block_depth = block.depth
                block_branches_seen[block_depth] = block_id
                parent_depth = block_depth - 1

                if parent_depth in block_branches_seen:
                    parent_id = block_branches_seen[parent_depth]
                    branches.append(
                        {
                            "uuid": block_id,
                            "parent": parent_id,
                            "position": position,
                            "depth": block.depth,
                        }
                    )

        return pd.DataFrame(branches)

    @property
    def block_links(self) -> pd.DataFrame:
        """Return a DataFrame of all block links in the graph."""
        return pd.DataFrame(
            [
                {"source": str(block.id), "target": str(link.target)}
                for block in self.graph.blocks.values()
                for link in block.block_links
                if link.target in self.graph.blocks
            ],
        )

    @property
    def block_properties(self) -> pd.DataFrame:
        """Return a DataFrame of all block properties in the graph."""
        return pd.DataFrame(
            [
                {"block": str(block.id), "property": prop.field, "value": prop.value}
                for block in self.graph.blocks.values()
                for prop in block.properties.values()
            ],
        )

    @property
    def blocks(self) -> pd.DataFrame:
        """Return a DataFrame of all blocks in the graph."""
        return pd.DataFrame(
            [
                {
                    "uuid": str(block.id),
                    "content": block.content,
                    "is_heading": cast(bool, block.is_heading),
                    "directive": block.directive,
                }
                for block in self.graph.blocks.values()
            ],
        )

    @property
    def links(self) -> pd.DataFrame:
        """Return a DataFrame of all links in the graph."""
        return pd.DataFrame(
            [
                {"source": str(block.id), "target": link.target}
                for block in self.graph.blocks.values()
                for link in block.links
            ],
        )

    @property
    def namespaces(self) -> pd.DataFrame:
        """Return a DataFrame of all namespaces in the graph."""
        return pd.DataFrame(
            [
                {"page": page.name, "namespace": page.namespace}
                for page in self.graph.pages.values()
                if page.namespace != NAMESPACE_SELF
            ],
        )

    @property
    def pages(self) -> pd.DataFrame:
        """Return a DataFrame of all pages in the graph."""
        return pd.DataFrame(
            [
                {
                    "name": page.name,
                    "is_placeholder": page.is_placeholder,
                    "is_public": page.is_public,
                }
                for page in self.graph.pages.values()
            ]
        )

    @property
    def page_memberships(self) -> pd.DataFrame:
        """Return a DataFrame of all page memberships in the graph."""
        return pd.DataFrame(
            [
                {
                    "page": page.name,
                    "block": str(block.id),
                    "position": position,
                    "depth": block.depth,
                }
                for page in self.graph.pages.values()
                for position, block in enumerate(page.blocks)
            ]
        )

    @property
    def page_properties(self) -> pd.DataFrame:
        """Return a DataFrame of all page properties in the graph."""
        return pd.DataFrame(
            [
                {"page": page.name, "property": prop.field, "value": prop.value}
                for page in self.graph.pages.values()
                for prop in page.properties.values()
            ],
        )

    @property
    def page_tags(self) -> pd.DataFrame:
        """Return a DataFrame of all page tags in the graph."""
        return pd.DataFrame(
            [
                {"page": page.name, "tag": tag}
                for page in self.graph.pages.values()
                for tag in page.tags
            ],
        )

    @property
    def resource_links(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """Return a DataFrame of all resource links in the graph."""
        resource_links = []
        resources_seen = {}

        for page in self.graph.pages.values():
            for block in page.blocks:
                block_id = str(block.id)

                for link in block.resource_links:
                    target = link.target
                    is_asset = target in self.graph.assets
                    resources_seen[target] = is_asset
                    resource_links.append(
                        {
                            "source": block_id,
                            "target": target,
                            "label": link.link_text,
                        }
                    )

        resources = [
            {"path": resource, "is_asset": is_asset}
            for resource, is_asset in resources_seen.items()
        ]

        return pd.DataFrame(resources), pd.DataFrame(resource_links)

    @property
    def tag_links(self) -> pd.DataFrame:
        """Return a DataFrame of all tag links in the graph."""
        return pd.DataFrame(
            [
                {"source": str(block.id), "target": link.target, "as_tag": True}
                for block in self.graph.blocks.values()
                for link in block.tag_links
            ],
        )
