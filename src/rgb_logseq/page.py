"""Logseq page handling."""

from pathlib import Path

from pydantic import BaseModel, computed_field

from .block import Block, find_blocks
from .const import logger
from .link import DirectLink
from .property import Property

NAMESPACE_SELF = "."


class Page(BaseModel):
    """A full Logseq page."""

    blocks: list[Block]
    name: str
    properties: dict[str, Property]

    # True if this should not be treated as a full Page by handlers.
    is_placeholder: bool = False

    @computed_field
    def is_public(self) -> bool:
        """Return True if this page's root content is public."""
        if "public" not in self.properties:
            return False

        return self.properties["public"].is_true

    @property
    def links(self) -> list[DirectLink]:
        """Return all DirectLink objects found in this Page."""
        return [link for block in self.blocks for link in block.links]

    @property
    def namespace(self) -> str:
        """
        Return name of parent page in namespace hierarchy.

        We derive the namespace parent from the Page name when treated as a
        Path object. If there is no parent, this returns ``NAMESPACE_SELF``.
        It's an awkward special case, but is at least more consistent than
        returning None for no parent. It also leaves room for definining an
        ad hoc root page in the graph later.

        .. note::

          This behavior probably needs to be double-checked in Windows, though
          Windows handles UNIX-style path separators just fine these days.
        """
        return str(Path(self.name).parent)

    @property
    def tags(self) -> list[str]:
        """Return tags directly associated with this page."""
        if "tags" not in self.properties:
            return []

        tag_prop = self.properties["tags"]
        return [tag.strip() for tag in tag_prop.value.split(",")]

    def add_block(self, block: Block) -> None:
        """Add a Block to the end of this Page."""
        self.blocks.append(block)

    def block_memberships_for_kuzu(self) -> list[dict[str, str | int]]:
        """Return a list of block memberships for Kuzu."""
        return [
            {
                "block": str(block.id),
                "page": self.name,
                "depth": block.depth,
                "position": position,
            }
            for position, block in enumerate(self.blocks)
        ]


def parse_page_text(text: str, name: str) -> Page:
    """Initialize a Page from a text string of Logseq blocks."""
    try:
        blocks = find_blocks(text)
    except ValueError as e:
        logger.error("Error finding blocks in %s", name)
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
