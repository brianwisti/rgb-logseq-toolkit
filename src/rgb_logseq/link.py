"""Graph Link and embed functionality."""

from enum import Enum

from pydantic import BaseModel


class GraphLinkType(str, Enum):
    link = "link"
    tag = "tag"
    attribute = "attribute"
    embed = "embed"


class GraphLink(BaseModel):
    """A single connection between two points on a Graph."""

    target: str
    link_text: str | None = None
    link_type: GraphLinkType = GraphLinkType.link

    @property
    def label(self) -> str:
        """The title used for the link target."""
        if self.link_text is not None:
            return self.link_text

        return self.target
