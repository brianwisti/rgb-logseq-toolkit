"""Explore my Logseq graph in Kuzu."""

from pathlib import Path
import os

from dotenv import load_dotenv
import kuzu
import polars

from .const import logger
from .graph import Graph
from .page import load_page_file

PAGE_SCHEMA = """
    create node table Page(
        name string,
        is_placeholder boolean,
        is_public boolean,
        primary key (name)
    )
"""

PROPERTY_SCHEMA = """
    create node table Property(
        name string,
        primary key(name)
    )
"""

LINKS_SCHEMA = """
    create rel table Links(
        from Page to Page
    )
"""

PAGE_PROPERTIES_SCHEMA = """
    create rel table PageHasProperty(
        from Page to Property,
        value string
    )
"""
load_dotenv()


def load_graph(graph_path: Path) -> Graph:
    """Load pages in Graph."""
    logger.info("path: %s", graph_path)
    graph = Graph()
    page_folders = ["journals", "pages"]

    for folder in page_folders:
        subfolder = graph_path / folder
        for md_path in subfolder.glob("./**/*.md"):
            logger.debug("md path: %s", md_path)
            page = load_page_file(md_path)
            logger.debug("page: %s", page)
            graph.add_page(page)

    return graph


def create_db() -> kuzu.Connection:
    db = kuzu.Database("./graph_db")
    conn = kuzu.Connection(db)
    conn.execute(PAGE_SCHEMA)
    conn.execute(LINKS_SCHEMA)
    conn.execute(PROPERTY_SCHEMA)
    conn.execute(PAGE_PROPERTIES_SCHEMA)

    return conn


def main() -> None:
    """Do interesting stuff."""
    graph_path = os.getenv("GRAPH_PATH")
    assert graph_path

    csv_options = {
        "include_header": False,
        "quote_style": "non_numeric",
    }
    pages_path = Path(graph_path).expanduser()
    graph = load_graph(pages_path)
    graph_name = pages_path.stem
    logger.info("Loaded graph %s; %s pages", graph_name, len(graph.pages))

    pages = [
        {
            "name": page.name,
            "is_placeholder": page.is_placeholder,
            "is_public": page.is_public,
        }
        for page in graph.pages.values()
    ]
    polars.DataFrame(pages).write_csv("page.csv", **csv_options)

    links = graph.links
    polars.DataFrame(links).write_csv("links.csv", **csv_options)

    page_properties = set()
    pages_with_properties = []

    for prop, pages_with_prop in graph.page_properties.items():
        page_properties.add(prop)
        # Tweaking nested strings until Kuzu issue #3461 is resolved.
        # - https://github.com/kuzudb/kuzu/issues/3461
        pages_with_properties += [
            {"from": page, "to": prop, "value": value.replace('"', "*")}
            for page, value in pages_with_prop.items()
        ]

    polars.DataFrame(list(page_properties)).write_csv("property.csv", **csv_options)
    polars.DataFrame(pages_with_properties).write_csv(
        "page_properties.csv", **csv_options
    )

    conn = create_db()
    conn.execute('COPY Page from "page.csv"')
    conn.execute('COPY Links from "links.csv"')
    conn.execute('COPY Property from "property.csv"')
    conn.execute('COPY PageHasProperty from "page_properties.csv"')


if __name__ == "__main__":
    main()
