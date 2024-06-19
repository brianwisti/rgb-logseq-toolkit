"""Loading and processing Logseq blocks."""

from __future__ import annotations

import re
import uuid
from typing import cast

from pydantic import BaseModel, computed_field

from .const import logger
from .line import Line, parse_line
from .link import BlockLink, DirectLink, ResourceLink
from .property import Property, ValueList

ATX_HEADER = re.compile(
    r"""^ \#{1,6} \s """,
    re.VERBOSE,
)


def toggle(value: bool) -> bool:
    """
    Return the opposite of the boolean handed in.

    Just here for slightly more readable main logic.
    """
    return not value


class BlockDepthError(Exception):
    """Error raised when a block is created with mismatched line depths."""


class Block(BaseModel):
    """A single block and its children."""

    lines: list[Line]
    properties: dict[str, Property]
    has_code_block: bool
    directive: str = ""
    parent: Block | None = None
    branches: list[Block] = []
    _id: uuid.UUID | None = None

    @computed_field
    def content(self) -> str:
        """Return the renderable content of lines as newline-separated string."""
        return "\n".join(
            [block_line.content for block_line in self.lines if block_line.is_content]
        )

    @property
    def block_links(self) -> list[BlockLink]:
        """Return a list of all block links found in this block."""
        gathered = []
        in_code = False

        for line in self.lines:
            if line.is_code_fence:
                in_code = not in_code

            if not in_code:
                for link in line.block_links:
                    gathered.append(link)

        return gathered

    @property
    def depth(self) -> int:
        """Return the tree depth of this block."""
        return self.lines[0].depth

    @computed_field
    def id(self) -> uuid.UUID:
        """
        Return this Block's unique ID.

        If there's an ``id`` property for this block, use that. Otherwise
        use the object's generated ID.
        """
        if self._id is None:
            if "id" in self.properties:
                self._id = uuid.UUID(hex=self.properties["id"].value)
            else:
                self._id = uuid.uuid4()

        return self._id

    @property
    def is_directive(self) -> bool:
        """Return true if this Block is a Logseq directive."""
        return bool(self.directive)

    @computed_field
    def is_heading(self) -> bool:
        """
        Return True if this Block marks a page section heading.

        For consistency I lean on the ``heading:: true`` property. As I'm
        inconsistent in my own graph we respect ATX-style headings, though
        with a logged warning.
        """
        if ATX_HEADER.match(str(self.content)):
            logger.debug("ATX Header in block: %s", self.content)
            return True

        if "heading" not in self.properties:
            return False

        return self.properties["heading"].is_true

    @property
    def is_public(self) -> bool:
        """Return true if this Block is public."""
        if "public" not in self.properties:
            return False

        return self.properties["public"].is_true

    @property
    def links(self) -> list[DirectLink]:
        """return a list of all graph links found in this block."""
        gathered = []
        in_code = False

        for line in self.lines:
            if line.is_code_fence:
                in_code = not in_code

            if not in_code:
                for link in line.links:
                    gathered.append(link)

        return gathered

    @property
    def raw(self) -> str:
        """Return the raw content of this Block's lines as a newline-separated string."""
        return "\n".join([block_line.raw for block_line in self.lines])

    @property
    def resource_links(self) -> list[ResourceLink]:
        """Return a list of all resource links found in this block."""
        gathered = []
        in_code = False

        for line in self.lines:
            if line.is_code_fence:
                in_code = not in_code

            if not in_code:
                for link in line.resource_links:
                    gathered.append(link)

        return gathered

    @property
    def tag_links(self) -> list[DirectLink]:
        """Return a list of all tag links found in this block."""
        gathered = []
        in_code = False

        for line in self.lines:
            if line.is_code_fence:
                in_code = not in_code

            if not in_code:
                for link in line.tag_links:
                    gathered.append(link)

        return gathered

    @property
    def tags(self) -> ValueList:
        """Return the list of string tag properties for this Block."""

        if "tags" not in self.properties:
            return []

        return self.properties["tags"].as_list()

    def for_kuzu(self) -> dict[str, str | bool | None]:
        """Return a dictionary of properties for Kuzu."""
        return {
            "uuid": str(self.id),
            "content": cast(str, self.content),
            "is_heading": cast(bool, self.is_heading),
            "directive": self.directive,
        }

    def has_property(self, field_name: str) -> bool:
        """Return True if the given property has been defined for this Block."""
        return field_name in self.properties


class BlockTree(BaseModel):
    """An ordered, nested collection of Logseq blocks."""

    branches: list[Block] = []

    @classmethod
    def from_text(cls, source: str) -> BlockTree:
        """Extract Logseq blocks from source text."""
        if len(source) == 0:
            # Handle empty blocks
            return BlockTree(branches=[from_lines([parse_line(source)])])

        blocks = []
        block_lines: list[Line] = []
        parsed_lines = [parse_line(line) for line in source.splitlines()]

        for line in parsed_lines:
            if line.is_block_opener:
                if block_lines:
                    blocks.append(from_lines(block_lines))
                    block_lines = []
            elif line.depth > 0 and not block_lines:
                raise BlockDepthError(
                    "First line in block may not be branch continuation"
                )

            block_lines.append(line)

        if block_lines:
            blocks.append(from_lines(block_lines))

        branches = find_branches(blocks)

        return BlockTree(branches=branches)


def find_branches(blocks: list[Block]) -> list[Block]:
    """Return a list of all branch blocks in the given list of blocks."""
    # Recursively construct blocks in branches and their children
    # based on the depth of each block.
    branches: list[Block] = []

    for block in blocks:
        branch_parent = None

        if branches:
            # Find the parent block
            branch_parent = branches[-1]

            while branch_parent and branch_parent.depth >= block.depth:
                branch_parent = branch_parent.parent

        if branch_parent:
            branch_parent.branches.append(block)
        else:
            branches.append(block)

    return branches


def find_blocks(source: str) -> BlockTree:
    """Extract Logseq blocks from source text."""
    return BlockTree.from_text(source)


def from_lines(lines: list[Line]) -> Block:
    """Create a Block from a list of Line objects."""
    has_code_block = False
    in_code_block = False
    in_directive = False
    directive = ""
    properties = {}
    depth = lines[0].depth

    for line in lines:
        if line.depth != depth:
            logger.error("Line <%s> depth does not match line <%s>", line, lines[0])
            raise ValueError("Line depth mismatch in Block.from_lines")

        if line.is_code_fence:
            has_code_block = True
            in_code_block = toggle(in_code_block)

        if line.is_property and not in_code_block:
            prop = line.as_property()
            properties[prop.field] = prop
        elif line.is_directive_opener:
            in_directive = True
            directive = line.directive
        elif line.is_directive_closer:
            if not in_directive:
                raise ValueError("Closing an unopened directive")

            in_directive = False

    if in_code_block:
        logger.error("Unclosed code block in: %s", lines)
        raise ValueError("unclosed code block")

    if in_directive:
        raise ValueError("Unclosed directive")

    return Block(
        lines=lines,
        properties=properties,
        has_code_block=has_code_block,
        directive=directive,
    )
