"""Loading and processing Logseq blocks."""

from pydantic import BaseModel

from .const import logger
from .line import Line, parse_line
from .link import DirectLink
from .property import Property, ValueList


def toggle(value: bool) -> bool:
    """
    Return the opposite of the boolean handed in.

    Just here for slightly more readable main logic.
    """
    return not value


class BlockDepthError(Exception):
    """Error raised when a block is created with mismatched line depths."""


class Block(BaseModel):
    """A single block of a Logseq page."""

    lines: list[Line]
    properties: dict[str, Property]
    has_code_block: bool
    directive: str | None = None

    @property
    def content(self) -> str:
        """Return the renderable content of lines as newline-separated string."""
        return "\n".join(
            [block_line.content for block_line in self.lines if block_line.is_content]
        )

    @property
    def depth(self) -> int:
        """Return the tree depth of this block."""
        return self.lines[0].depth

    @property
    def is_directive(self) -> bool:
        """Return true if this Block is a Logseq directive."""
        return bool(self.directive)

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
    def tags(self) -> ValueList:
        """Return the list of string tags for this Block."""

        if "tags" not in self.properties:
            return []

        return self.properties["tags"].as_list()

    def has_property(self, field_name: str) -> bool:
        """Return True if the given property has been defined for this Block."""
        return field_name in self.properties


def find_blocks(source: str) -> list[Block]:
    """Extract Logseq blocks from source text."""
    blocks = []
    block_lines = []

    if len(source) == 0:
        block_lines = [parse_line(source)]
    else:
        text_lines = source.splitlines()
        for text_line in text_lines:
            line = parse_line(text_line)

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

    return blocks


def from_lines(lines: list[Line]) -> Block:
    """Create a Block from a list of Line objects."""
    has_code_block = False
    in_code_block = False
    in_directive = False
    directive = None
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
