"""Functions and classes for exporting to a static site generator."""

from pydantic import BaseModel
from slugify import slugify

from .graph import Graph

PageMap = dict[str, str]


class Publisher(BaseModel):
    """Manages publishing a complete graph to SSG content folder."""

    graph: Graph
    _page_map: PageMap = {}

    @property
    def page_map(self) -> PageMap:
        """Return a mapping of page names to output slugs."""

        if not self._page_map:
            self._page_map = {name: page_slug(name) for name in self.graph.pages}

        return self._page_map


def page_slug(page_name: str) -> str:
    """Return the destination path for a given page name."""
    separator = "/"
    return separator.join([slugify(step) for step in page_name.split(separator)])
