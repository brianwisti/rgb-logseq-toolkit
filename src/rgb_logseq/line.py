"""Logseq line parsing logic."""

import logging
import re

from pydantic import BaseModel
from rich.logging import RichHandler

from .const import (
    MARK_BLOCK_CONTINUATION,
    MARK_BLOCK_INDENT,
    MARK_BLOCK_OPENER,
    MARK_CODE_FENCE,
    MARK_DIRECTIVE_CLOSER,
    MARK_DIRECTIVE_OPENER,
    MARK_DIRECTIVE_SPLIT,
    MARK_PROPERTY,
)
from .link import GraphLink
from .property import Property

logging.basicConfig(level=logging.INFO, handlers=[RichHandler()])

LINK_PATTERN = re.compile(
    r"""
        (?<! ` )
        \[\[
            (?P<target>[^\]]+)
        \]\]
                          """,
    re.VERBOSE,
)


class Line(BaseModel):
    """
    A single processed line of text from a Logseq page.

    A subatomic particle of our construction. We discard Line objects after
    they help us construct a Block.
    """

    raw: str
    content: str

    @property
    def depth(self) -> int:
        """Return the number of parent Blocks this Line has."""
        unindented = self.__unindented()
        line_depth = len(self.raw) - len(unindented)

        if unindented.startswith(MARK_BLOCK_OPENER):
            line_depth += 1
        elif unindented.startswith(MARK_BLOCK_CONTINUATION):
            line_depth += 1
        elif unindented == "-":
            logging.debug("Empty branch line")
            line_depth += 1

        return line_depth

    @property
    def directive(self) -> str | None:
        """
        Return the directive opened or closed by this line.

        If none, return None.
        """
        if self.is_directive_opener or self.is_directive_closer:
            return self.content.split(MARK_DIRECTIVE_SPLIT)[1]

        return None

    @property
    def is_code_fence(self) -> bool:
        """Return True if this Line indicates a code block boundary."""
        return self.content.startswith(MARK_CODE_FENCE)

    @property
    def is_content(self) -> bool:
        """Return True if this Line includes renderable content."""
        if self.is_property:
            return False

        if self.is_directive_opener or self.is_directive_closer:
            return False

        return True

    @property
    def is_block_opener(self) -> bool:
        """Return True if this line opens a new branch block."""
        content = self.__unindented()
        return content.startswith("-")

    @property
    def is_directive_opener(self) -> bool:
        """Return True if this line opens a new directive."""
        return self.content.startswith(MARK_DIRECTIVE_OPENER)

    @property
    def is_directive_closer(self) -> bool:
        """Return True if this line closes a directive block."""
        return self.content.startswith(MARK_DIRECTIVE_CLOSER)

    @property
    def is_empty(self) -> bool:
        """Return True if this line contains no content."""
        return self.content == ""

    @property
    def is_property(self) -> bool:
        """Return True if this line indicates a Block property."""
        return MARK_PROPERTY in self.content and not self.is_code_fence

    @property
    def links(self) -> list[GraphLink]:
        """Return a list of graph links contained in this Line."""
        link_matches = LINK_PATTERN.findall(self.content)
        return [GraphLink(target=target) for target in link_matches]

    def as_property(self) -> Property:
        """
        Return a Property object from this Line if possible.

        Raise an exception otherwise.
        """
        if not self.is_property:
            raise ValueError("Attempt to get non-property line as Property")

        return Property.loads(self.content)

    def __unindented(self) -> str:
        """Return raw source without leading indent markers."""
        return self.raw.lstrip(MARK_BLOCK_INDENT)


def parse_line(source: str) -> Line:
    """Parse a single line of text from a Logseq page."""
    content = source

    while content.startswith(MARK_BLOCK_INDENT):
        content = content[1:]

    if content == MARK_BLOCK_OPENER:
        logging.debug("Empty branch line")
        content = ""
    elif content.startswith(MARK_BLOCK_OPENER):
        content = content[2:]
    elif content.startswith(MARK_BLOCK_CONTINUATION):
        content = content[2:]

    return Line(
        raw=source,
        content=content,
    )


def parse_lines(lines: list[str]) -> list[Line]:
    """Parse a list of text lines from a Logseq page."""
    return [parse_line(line) for line in lines]
