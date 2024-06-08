"""Logseq line parsing logic."""

import re
import uuid

from pydantic import BaseModel

from .const import (
    MARK_BLOCK_CONTINUATION,
    MARK_BLOCK_INDENT,
    MARK_BLOCK_OPENER,
    MARK_CODE_FENCE,
    MARK_DIRECTIVE_CLOSER,
    MARK_DIRECTIVE_OPENER,
    MARK_DIRECTIVE_SPLIT,
    MARK_PROPERTY,
    logger,
)
from .link import BlockLink, DirectLink
from .property import Property

LINK_PATTERN = re.compile(
    r"""
        (?<! [`\#] )
        \[\[
            (?P<target>[^\]]+)
        \]\]
    """,
    re.VERBOSE,
)

BLOCK_LINK_PATTERN = re.compile(
    r"""
        (?<! [`\#] )
        \(\(
            (?P<target>[^\)]+)
        \)\)
    """,
    re.VERBOSE,
)

TAG_LINK_PATTERN = re.compile(
    r"""
        (?<! ` )
        \#
        (?:
            ( \w+ )
            |
            (?: \[\[ ( [^\]]+ ) \]\])
        )
        (?<! ` )
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

    @property
    def block_links(self) -> list[BlockLink]:
        """Return a list of links to specific blocks in this Line."""
        link_matches = BLOCK_LINK_PATTERN.findall(self.content)

        return [BlockLink(target=uuid.UUID(target)) for target in link_matches]

    @property
    def content(self) -> str:
        """Return line text without graph structure indicators."""
        unindented = self.__unindented()

        if not unindented:
            return ""

        if unindented == MARK_BLOCK_OPENER:
            return ""

        if unindented[0] in [MARK_BLOCK_OPENER, MARK_BLOCK_CONTINUATION]:
            return unindented[2:]

        return unindented

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
            logger.debug("Empty branch line")
            line_depth += 1

        return line_depth

    @property
    def directive(self) -> str:
        """
        Return the directive opened or closed by this line.

        If none, return an empty string.
        """
        if self.is_directive_opener or self.is_directive_closer:
            return self.content.split(MARK_DIRECTIVE_SPLIT)[1]

        return ""

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
    def links(self) -> list[DirectLink]:
        """Return a list of graph links contained in this Line."""
        link_matches = LINK_PATTERN.findall(self.content)
        return [DirectLink.to_page(target) for target in link_matches]

    @property
    def tag_links(self) -> list[DirectLink]:
        """Return a list of tag links contained in this line."""
        tag_links = []
        tag_link_matches = TAG_LINK_PATTERN.findall(self.content)

        if tag_link_matches:
            logger.debug("Found tags in: %s", self.content)

            for as_link, as_word in tag_link_matches:
                target = as_word if as_word else as_link
                logger.debug("using <%s> as tag target", target)

                if not target:
                    logger.error(
                        "Tag link without target in matches: %s", tag_link_matches
                    )

                tag_links.append(DirectLink.as_tag(target))

        return tag_links

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
    return Line(
        raw=source,
    )


def parse_lines(lines: list[str]) -> list[Line]:
    """Parse a list of text lines from a Logseq page."""
    return [parse_line(line) for line in lines]
