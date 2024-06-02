"""Graph Link and embed functionality."""

from pydantic import BaseModel


class DirectLink(BaseModel):
    """An explicit connection between two Pages on a Graph."""

    target: str
    link_text: str | None = None

    @property
    def label(self) -> str:
        """The title used for the link target."""
        if self.link_text is not None:
            return self.link_text

        return self.target
