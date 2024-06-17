"""Functions and classes for exporting to a static site generator."""

from slugify import slugify


def page_slug(page_name: str) -> str:
    """Return the destination path for a given page name."""
    separator = "/"
    return separator.join([slugify(step) for step in page_name.split(separator)])
