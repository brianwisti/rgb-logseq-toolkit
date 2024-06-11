"""Graph Link and embed functionality."""

import uuid
from enum import Enum

from pydantic import BaseModel


class LinkType(Enum):
    """Specifies what a DirectLink points at."""

    PAGE = 0
    TAG = 1


class DirectLink(BaseModel):
    """An explicit connection to another node on the Graph."""

    target: str
    link_type: LinkType
    link_text: str | None = None

    @classmethod
    def as_tag(cls, tag: str) -> "DirectLink":
        """Return a page link that's been presented as a tag."""
        return cls(target=tag, link_type=LinkType.TAG)

    @classmethod
    def to_page(cls, page_name: str, link_text: str | None = None) -> "DirectLink":
        """Return a direct link to a graph page."""
        return cls(target=page_name, link_text=link_text, link_type=LinkType.PAGE)

    @property
    def label(self) -> str:
        """The title used for the link target."""
        if self.link_text is not None:
            return self.link_text

        return self.target


class BlockLink(BaseModel):
    """An explicit connection to a Block on the Graph."""

    target: uuid.UUID


class ResourceLink(BaseModel):
    """A connection to a resource outside the graph pages."""

    target: str
    link_text: str
    is_embed: bool = False
