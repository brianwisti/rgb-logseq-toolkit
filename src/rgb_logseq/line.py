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
    depth: int
    is_block_opener: bool
    is_directive_opener: bool
    is_directive_closer: bool
    directive: str | None = None
    links: list[GraphLink] = []

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
    def is_empty(self) -> bool:
        """Return True if this line contains no content."""
        return self.content == ""

    @property
    def is_property(self) -> bool:
        """Return True if this line indicates a Block property."""
        return MARK_PROPERTY in self.content and not self.is_code_fence

    def as_property(self) -> Property:
        """
        Return a Property object from this Line if possible.

        Raise an exception otherwise.
        """
        if not self.is_property:
            raise ValueError("Attempt to get non-property line as Property")

        return Property.loads(self.content)


def parse_line(source: str) -> Line:
    """Parse a single line of text from a Logseq page."""
    content = source
    depth = 0
    is_block_opener = False
    is_directive_opener = False
    is_directive_closer = False
    directive = None
    links = []

    while content.startswith(MARK_BLOCK_INDENT):
        content = content[1:]
        depth += 1

    if content.startswith(MARK_BLOCK_OPENER):
        content = content[2:]
        depth += 1
        is_block_opener = True
    elif content.startswith(MARK_BLOCK_CONTINUATION):
        content = content[2:]
        depth += 1

    if content.startswith(MARK_DIRECTIVE_OPENER):
        is_directive_opener = True
        _, directive = content.split(MARK_DIRECTIVE_SPLIT)
    elif content.startswith(MARK_DIRECTIVE_CLOSER):
        is_directive_closer = True
        _, directive = content.split(MARK_DIRECTIVE_SPLIT)
    elif link_matches := LINK_PATTERN.findall(content):
        links = [GraphLink(target=target) for target in link_matches]
    elif content == "-":
        logging.debug("Empty branch line")
        content = ""
        depth += 1
        is_block_opener = True

    return Line(
        raw=source,
        content=content,
        depth=depth,
        is_block_opener=is_block_opener,
        is_directive_opener=is_directive_opener,
        is_directive_closer=is_directive_closer,
        directive=directive,
        links=links,
    )


def parse_lines(lines: list[str]) -> list[Line]:
    """Parse a list of text lines from a Logseq page."""
    return [parse_line(line) for line in lines]
