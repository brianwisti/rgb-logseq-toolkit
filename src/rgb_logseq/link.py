"""Graph Link and embed functionality."""

from pydantic import BaseModel


class DirectLink(BaseModel):
    """An explicit connection to another Page on a Graph."""

    target: str
    link_text: str | None = None

    @property
    def label(self) -> str:
        """The title used for the link target."""
        if self.link_text is not None:
            return self.link_text

        return self.target


class TagLink(DirectLink):
    """A tagged connection to another Page on a Graph."""

    @property
    def label(self) -> str:
        """
        Return the title used for the link target.

        Tags use simpler labeling: just the target page.
        """
        return self.target
