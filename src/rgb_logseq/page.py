"""Logseq page handling."""

from __future__ import annotations

import logging
from pathlib import Path

from pydantic import BaseModel
from rich.logging import RichHandler

from .block import Block, find_blocks
from .link import GraphLink
from .property import Property

logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])


class Page(BaseModel):
    """A full Logseq page."""

    blocks: list[Block]
    name: str
    properties: dict[str, Property]

    @property
    def is_public(self) -> bool:
        """Return True if this page's root content is public."""
        if "public" not in self.properties:
            return False

        return self.properties["public"].is_true

    @property
    def links(self) -> list[GraphLink]:
        """Return all GraphLink objects found in this Page."""
        return [link for block in self.blocks for link in block.links]

    def add_block(self, block: Block) -> None:
        """Add a Block to the end of this Page."""
        self.blocks.append(block)


def parse_page_text(text: str, name: str) -> Page:
    """Initialize a Page from a text string of Logseq blocks."""
    try:
        blocks = find_blocks(text)
    except ValueError as e:
        logging.error("Error finding blocks in %s", name)
        raise e
    properties = {}
    first_block = blocks[0]

    if first_block.depth == 0:
        properties = first_block.properties

    return Page(blocks=blocks, name=name, properties=properties)


def load_page_file(path: Path) -> Page:
    """Initalizae a Page from a file on disk."""
    name = path.stem.replace("___", "/").replace("_", "/")
    text = path.read_text(encoding="utf-8")
    return parse_page_text(text, name=name)
